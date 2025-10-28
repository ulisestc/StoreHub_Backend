from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from django.db.models import Sum, Count
from django.utils.dateparse import parse_date
from products.serializers import ProductSerializer
from sales.models import Sale, SaleDetail
from products.models import Product

class SalesByDateReport(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        start_date_str = request.query_params.get('start_date')
        end_date_str = request.query_params.get('end_date')

        if not start_date_str or not end_date_str:
            return Response({"error": "Fechas 'start_date' y 'end_date' son requeridas (YYYY-MM-DD)"}, status=400)

        sales = Sale.objects.filter(created_at__range=[start_date_str, end_date_str])
        report = sales.aggregate(
            total_ventas=Sum('total'),
            total_subtotal=Sum('subtotal'),
            total_impuestos=Sum('impuestos'),
            num_transacciones=Count('id')
        )
        return Response(report)

class TopProductsReport(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        limit_str = request.query_params.get('limit', 10)
        top_products = SaleDetail.objects.values('product__name') \
            .annotate(total_vendido=Sum('quantity')) \
            .order_by('-total_vendido')[:int(limit_str)]
        return Response(top_products)
    
class LowStockProductsReport(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        threshold = request.query_params.get('threshold', 10)
        #corroboramos que es int
        try: 
            threshold = int(threshold)
        except ValueError:
            return Response({"error": "El parámetro 'threshold' debe ser un número entero."}, status=400)
        
        low_stock_products = Product.objects.filter(stock__lt=threshold, is_active= True).order_by('stock')
        low_stock_products_serialized = ProductSerializer(low_stock_products, many=True)
        return Response(low_stock_products_serialized.data)

