from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from .models import Sale, SaleDetail
from rest_framework import viewsets, serializers, mixins
from rest_framework.permissions import IsAuthenticated
from .serlializers import SaleSerializer, SaleDetailSerializer

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
                
                total_sale = 0
                sale_details_to_create = []

                for detail_data in details_data:
                    product = detail_data['product']
                    quantity = detail_data['quantity']
                    price_at_sale = product.price

                    # Actualiza el stock del producto
                    product.stock -= quantity
                    product.save()

                    # total de la venta
                    total_sale += price_at_sale * quantity
                    
                    # Prepara el objeto SaleDetail para crearlo después
                    sale_details_to_create.append(
                        SaleDetail(
                            product=product,
                            quantity=quantity,
                            price_at_sale=price_at_sale
                        )
                    )

                #Instancia la venta con todo y detalles
                sale = serializer.save(user=self.request.user, total=total_sale)

                for detail in sale_details_to_create:
                    detail.sale = sale
                
                SaleDetail.objects.bulk_create(sale_details_to_create)

        except Exception as e:
            raise serializers.ValidationError(f"Error al crear la venta: {str(e)}")
