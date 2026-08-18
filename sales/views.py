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
