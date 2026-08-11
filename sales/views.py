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
from decimal import Decimal 

class SaleViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet
):
    queryset = Sale.objects.all().order_by('-created_at')
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
                    #se va sumando el subtotal y 
                    subtotal_sale += detail_data['product'].price * detail_data['quantity']
                    product = detail_data['product']
                    quantity = detail_data['quantity']      
                    price_at_sale = product.price

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

                # Calcula impuestos y total
                impuestos_sale = subtotal_sale * impuestos
                total_sale = subtotal_sale + impuestos_sale

                #Instancia la venta con todo y detalles
                sale = serializer.save(user=self.request.user, total=total_sale, subtotal = subtotal_sale, impuestos=impuestos_sale)

                for detail in sale_details_to_create:
                    detail.sale = sale
                
                SaleDetail.objects.bulk_create(sale_details_to_create)

            # Envío de Ticket por Correo (Fuera de la transacción para asegurar que ya se guardó)
            if sale.client and sale.client.email:
                from django.core.mail import send_mail
                from django.conf import settings
                
                asunto = f"Tu Ticket de Compra en StoreHub - Venta #{sale.id}"
                
                # Construir el detalle
                detalles_texto = ""
                for detail in sale_details_to_create:
                    detalles_texto += f"- {detail.quantity}x {detail.product.name} = ${detail.quantity * detail.price_at_sale}\n"
                
                mensaje = (
                    f"¡Hola {sale.client.name}!\n\n"
                    f"Gracias por tu compra. Aquí tienes el resumen de tu ticket:\n\n"
                    f"{detalles_texto}\n"
                    f"Subtotal: ${sale.subtotal}\n"
                    f"Impuestos (IVA): ${sale.impuestos}\n"
                    f"Total Pagado: ${sale.total}\n\n"
                    f"¡Esperamos verte pronto!\n"
                )
                
                try:
                    send_mail(
                        asunto,
                        mensaje,
                        settings.EMAIL_HOST_USER,
                        [sale.client.email],
                        fail_silently=True,
                    )
                except Exception as mail_error:
                    print(f"No se pudo enviar el correo: {mail_error}")

        except Exception as e:
            raise serializers.ValidationError(f"Error al crear la venta: {str(e)}")

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
