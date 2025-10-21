from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from .models import Sale, SaleDetail
from rest_framework import viewsets, serializers, mixins
from rest_framework.permissions import IsAuthenticated
from .serializers import SaleSerializer, SaleDetailSerializer
from decimal import Decimal # <-- 1. Importar Decimal

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

        except Exception as e:
            raise serializers.ValidationError(f"Error al crear la venta: {str(e)}")
