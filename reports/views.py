from django.db.models import Sum, Count, F, FloatField
from django.db.models.functions import ExtractWeekDay, ExtractHour
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from accounts.permissions import IsAdminRole
from products.models import Product
from sales.models import Sale, SaleDetail

class SalesByDateReport(APIView):
    permission_classes = [IsAuthenticated, IsAdminRole]
    
    def get(self, request):
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        if not start_date or not end_date:
            return Response({"error": "Fechas 'start_date' y 'end_date' son requeridas (YYYY-MM-DD)"}, status=400)

        sales = Sale.objects.filter(created_at__range=[start_date, end_date], store=request.user.store)
        
        # 1. Agregaciones Básicas
        report = sales.aggregate(
            total_ventas=Sum('total'),
            total_subtotal=Sum('subtotal'),
            total_impuestos=Sum('impuestos'),
            num_transacciones=Count('id')
        )
        
        # Valores por defecto para evitar Nones
        total_ventas = report['total_ventas'] or 0.0
        num_transacciones = report['num_transacciones'] or 0
        
        # 2. Nuevos KPIs (Credit Scoring y Eficiencia)
        # ATV: Average Transaction Value (Ticket Promedio)
        atv = (total_ventas / num_transacciones) if num_transacciones > 0 else 0.0
        
        # UPT: Units Per Transaction
        total_items_sold = SaleDetail.objects.filter(sale__in=sales).aggregate(total=Sum('quantity'))['total'] or 0
        upt = (total_items_sold / num_transacciones) if num_transacciones > 0 else 0.0
        
        # Tasa de Lealtad: Porcentaje de transacciones con un Cliente asociado vs Ventas Anónimas
        sales_with_client = sales.filter(client__isnull=False).count()
        loyalty_rate = (sales_with_client / num_transacciones * 100) if num_transacciones > 0 else 0.0

        # Respuesta consolidada
        data = {
            "total_ventas": float(total_ventas),
            "num_transacciones": num_transacciones,
            "atv": float(atv),
            "upt": float(upt),
            "loyalty_rate": float(loyalty_rate)
        }
        
        return Response(data)

class TopProductsReport(APIView):
    permission_classes = [IsAuthenticated, IsAdminRole]
    
    def get(self, request):
        limit = int(request.query_params.get('limit', 10))
        top_products = SaleDetail.objects.filter(sale__store=request.user.store)\
            .values('product__name')\
            .annotate(total_vendido=Sum('quantity'))\
            .order_by('-total_vendido')[:limit]
            
        return Response(list(top_products))

class LowStockProductsReport(APIView):
    permission_classes = [IsAuthenticated, IsAdminRole]
    
    def get(self, request):
        try:
            threshold = int(request.query_params.get('threshold', 10))
        except ValueError:
            return Response({"error": "El parámetro 'threshold' debe ser un entero."}, status=400)

        low_stock = Product.objects.filter(stock__lt=threshold, is_active=True, store=request.user.store)\
            .values('id', 'name', 'sku', 'stock', 'price')\
            .order_by('stock')
            
        return Response(list(low_stock))

class InventoryValueReport(APIView):
    """
    Capital Inmovilizado: Calcula cuánto dinero tiene el negocio "congelado" en inventario.
    Fundamental para el análisis de liquidez en un perfil crediticio.
    """
    permission_classes = [IsAuthenticated, IsAdminRole]

    def get(self, request):
        value = Product.objects.filter(store=request.user.store, is_active=True).aggregate(
            total_value=Sum(F('stock') * F('cost_price'), output_field=FloatField())
        )
        total_value = value['total_value'] or 0.0
        return Response({"capital_inmovilizado": float(total_value)})

class SalesHeatmapReport(APIView):
    """
    Mapa de Calor: Muestra en qué días de la semana y horas hay mayor volumen de ventas.
    Útil para demostrar consistencia operativa y capacidad de pago en ciertas ventanas de tiempo.
    """
    permission_classes = [IsAuthenticated, IsAdminRole]

    def get(self, request):
        # 1 es Domingo, 2 es Lunes, etc.
        heatmap = Sale.objects.filter(store=request.user.store)\
            .annotate(day_of_week=ExtractWeekDay('created_at'), hour=ExtractHour('created_at'))\
            .values('day_of_week', 'hour')\
            .annotate(sales_count=Count('id'), total_revenue=Sum('total'))\
            .order_by('day_of_week', 'hour')
            
        return Response(list(heatmap))

