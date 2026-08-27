from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from .models import Sale, SaleDetail
from rest_framework import viewsets, serializers, mixins
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from .serializers import SaleSerializer, SaleDetailSerializer
from .tasks import send_ticket_email
from decimal import Decimal 

class SaleViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet
):
    def get_queryset(self):
        return Sale.objects.filter(store=self.request.user.store).order_by('-created_at')
    serializer_class = SaleSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        details_data = serializer.validated_data.pop('details')

        # Validaciones
        if not details_data:
            raise serializers.ValidationError("La venta debe tener al menos un detalle.")
        else:
            for detail_data in details_data:
                if detail_data['quantity'] <= 0:
                    raise serializers.ValidationError("La cantidad debe ser mayor a cero.")
                if detail_data['product'].stock < detail_data['quantity']:
                    raise serializers.ValidationError("No hay suficiente stock para el producto seleccionado.")
        # end validaciones -----------------------------

        try:
            with transaction.atomic():
                
                subtotal_sale = Decimal('0.0') # valor en brut0
                impuestos_sale = Decimal('0.0') #calculo de subtotal * impuesto
                impuestos = Decimal('0.16') # IVA MEXICO
                total_sale = Decimal('0.0') # subtotal + impuestos
                sale_details_to_create = []

                for detail_data in details_data:
                    product = detail_data['product']
                    quantity = detail_data['quantity']      
                    price_at_sale = product.price

                    # OXXO model: Product price already includes VAT.
                    item_total = price_at_sale * quantity
                    total_sale += item_total

                    # Actualiza el stock del producto
                    product.stock -= quantity
                    product.save()
                    
                    # Prepara el objeto SaleDetail para crearlo después
                    sale_details_to_create.append(
                        SaleDetail(
                            product=product,
                            quantity=quantity,
                            price_at_sale=price_at_sale
                        )
                    )

                # Calcula subtotal e impuestos (16% IVA) extraídos del total
                # Formula: Total = Subtotal * 1.16 => Subtotal = Total / 1.16
                subtotal_sale = total_sale / Decimal('1.16')
                impuestos_sale = total_sale - subtotal_sale

                #Instancia la venta con todo y detalles
                sale = serializer.save(user=self.request.user, store=self.request.user.store, total=total_sale, subtotal = subtotal_sale, impuestos=impuestos_sale)

                for detail in sale_details_to_create:
                    detail.sale = sale
                
                SaleDetail.objects.bulk_create(sale_details_to_create)

            # Envío de Ticket por Correo de forma asíncrona usando Celery
            send_ticket_email.delay(sale.id)

        except Exception as e:
            raise serializers.ValidationError(f"Error al crear la venta: {str(e)}")

    @action(detail=True, methods=['post'], url_path='send-ticket')
    def send_ticket(self, request, pk=None):
        sale = self.get_object()
        email_to = request.data.get('email')
        
        # Como es a demanda desde el historial, lo enviamos asíncrono también
        send_ticket_email.delay(sale.id, email_to=email_to)
        return Response({"message": "El correo está en proceso de envío."}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='bulk-sync')
    def bulk_sync(self, request):
        """
        Endpoint para recibir un lote de ventas realizadas offline (Service Workers).
        El cuerpo de la petición debe ser un arreglo de ventas.
        """
        sales_data = request.data
        if not isinstance(sales_data, list):
            return Response({"error": "Se esperaba un arreglo de ventas."}, status=status.HTTP_400_BAD_REQUEST)
        
        created_sales = []
        errors = []

        # Se hace una transacción completa: Si un lote falla por stock, todo falla
        # o podríamos aislar cada venta. Para sistemas offline suele ser mejor transacciones individuales
        # pero procesadas en bucle, para no perder las válidas.
        for index, sale_data in enumerate(sales_data):
            serializer = self.get_serializer(data=sale_data)
            if serializer.is_valid():
                try:
                    # Reutilizamos la lógica de perform_create pero manejamos la excepción
                    # Necesitamos emular la request para que perform_create pueda acceder a request.user
                    serializer.context['request'] = request
                    self.perform_create(serializer)
                    created_sales.append(serializer.data)
                except serializers.ValidationError as e:
                    errors.append({"index": index, "error": e.detail})
                except Exception as e:
                    errors.append({"index": index, "error": str(e)})
            else:
                errors.append({"index": index, "error": serializer.errors})
        
        return Response({
            "synced": len(created_sales),
            "errors": errors,
            "created_sales": [s.get('id') for s in created_sales]
        }, status=status.HTTP_207_MULTI_STATUS if errors else status.HTTP_201_CREATED)

from .models import CashRegisterSession
from .serializers import CashRegisterSessionSerializer
from django.utils import timezone
from django.db.models import Sum

class CashRegisterSessionViewSet(viewsets.ModelViewSet):
    serializer_class = CashRegisterSessionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return CashRegisterSession.objects.filter(store=self.request.user.store).order_by('-opened_at')

    @action(detail=False, methods=['post'], url_path='open')
    def open_session(self, request):
        store = request.user.store
        
        # Check if there's already an open session
        open_session = CashRegisterSession.objects.filter(store=store, closed_at__isnull=True).first()
        if open_session:
            return Response({"error": "Ya existe un turno de caja abierto."}, status=status.HTTP_400_BAD_REQUEST)
            
        opening_balance = request.data.get('opening_balance')
        if opening_balance is None:
            return Response({"error": "opening_balance es requerido."}, status=status.HTTP_400_BAD_REQUEST)
            
        session = CashRegisterSession.objects.create(
            store=store,
            opened_by=request.user,
            opening_balance=opening_balance,
            notes=request.data.get('notes', '')
        )
        serializer = self.get_serializer(session)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'], url_path='current')
    def current_session(self, request):
        store = request.user.store
        session = CashRegisterSession.objects.filter(store=store, closed_at__isnull=True).first()
        
        if not session:
            return Response({"message": "No hay turnos abiertos actualmente.", "session": None}, status=status.HTTP_200_OK)
            
        # Calculate expected closing balance
        # Sum of sales (cash) during the session. For now we assume all sales are cash.
        sales_total = Sale.objects.filter(
            store=store, 
            created_at__gte=session.opened_at
        ).aggregate(total=Sum('total'))['total'] or Decimal('0.0')
        
        expected = session.opening_balance + sales_total
        session.expected_closing_balance = expected
        session.save(update_fields=['expected_closing_balance'])
        
        serializer = self.get_serializer(session)
        return Response({"session": serializer.data}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='close')
    def close_session(self, request, pk=None):
        session = self.get_object()
        
        if session.closed_at is not None:
            return Response({"error": "Este turno de caja ya fue cerrado."}, status=status.HTTP_400_BAD_REQUEST)
            
        actual_closing_balance = request.data.get('actual_closing_balance')
        if actual_closing_balance is None:
            return Response({"error": "actual_closing_balance es requerido."}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            actual_closing_balance = Decimal(str(actual_closing_balance))
        except (ValueError, TypeError, Decimal.InvalidOperation):
            return Response({"error": "actual_closing_balance debe ser un número válido."}, status=status.HTTP_400_BAD_REQUEST)
            
        # Recalculate expected just to be sure
        sales_total = Sale.objects.filter(
            store=session.store, 
            created_at__gte=session.opened_at
        ).aggregate(total=Sum('total'))['total'] or Decimal('0.0')
        
        expected = session.opening_balance + sales_total
        
        session.expected_closing_balance = expected
        session.actual_closing_balance = actual_closing_balance
        session.closed_by = request.user
        session.closed_at = timezone.now()
        
        notes = request.data.get('notes')
        if notes:
            session.notes = f"{session.notes}\nCierre: {notes}" if session.notes else f"Cierre: {notes}"
            
        session.save()
        
        serializer = self.get_serializer(session)
        return Response(serializer.data, status=status.HTTP_200_OK)
