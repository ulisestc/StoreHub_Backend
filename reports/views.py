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

        return Response(list(heatmap))

import math
from collections import defaultdict
from itertools import combinations
from datetime import timedelta
from django.utils import timezone

class MarketBasketReport(APIView):
    """
    Algoritmo Apriori Simplificado (Market Basket Analysis)
    Encuentra qué productos se compran juntos frecuentemente.
    """
    permission_classes = [IsAuthenticated, IsAdminRole]

    def get(self, request):
        # 1. Obtener todas las ventas y sus productos
        # limitamos a los últimos 30 o 90 días para rendimiento en tiendas grandes
        days_ago = timezone.now() - timedelta(days=90)
        sales_data = SaleDetail.objects.filter(sale__store=request.user.store, sale__created_at__gte=days_ago)\
                                       .values_list('sale_id', 'product__name')
        
        # Agrupar productos por venta
        transactions = defaultdict(set)
        product_counts = defaultdict(int)
        
        for sale_id, product_name in sales_data:
            transactions[sale_id].add(product_name)

        total_transactions = len(transactions)
        if total_transactions == 0:
            return Response([])

        # Contar pares (A, B) y frecuencias individuales
        pair_counts = defaultdict(int)
        
        for sale_id, products in transactions.items():
            for p in products:
                product_counts[p] += 1
            
            # Combinaciones de pares en esta transacción
            for pair in combinations(sorted(products), 2):
                pair_counts[pair] += 1

        # Calcular métricas de asociación
        rules = []
        for (p1, p2), count in pair_counts.items():
            if count < 2:  # Ignorar si solo pasó 1 vez
                continue
                
            support = count / total_transactions
            
            # Confianza: Probabilidad de comprar p2 dado p1
            confidence_p1_to_p2 = count / product_counts[p1]
            
            # Confianza: Probabilidad de comprar p1 dado p2
            confidence_p2_to_p1 = count / product_counts[p2]
            
            rules.append({
                'product_a': p1,
                'product_b': p2,
                'times_bought_together': count,
                'support_percent': round(support * 100, 2),
                'confidence_a_to_b': round(confidence_p1_to_p2 * 100, 2),
                'confidence_b_to_a': round(confidence_p2_to_p1 * 100, 2)
            })
            
        # Ordenar por frecuencia
        rules = sorted(rules, key=lambda x: x['times_bought_together'], reverse=True)[:15]
        return Response(rules)

class SafetyStockReport(APIView):
    """
    Cálculo Científico del Inventario de Seguridad usando Desviación Estándar (Z-Score = 1.65 para 95%)
    """
    permission_classes = [IsAuthenticated, IsAdminRole]

    def get(self, request):
        days_ago = timezone.now() - timedelta(days=30)
        
        # Ventas agrupadas por producto y día
        from django.db.models.functions import TruncDate
        daily_sales = SaleDetail.objects.filter(sale__store=request.user.store, sale__created_at__gte=days_ago)\
            .annotate(date=TruncDate('sale__created_at'))\
            .values('product_id', 'product__name', 'product__stock', 'date')\
            .annotate(daily_sold=Sum('quantity'))
            
        product_data = defaultdict(lambda: {'name': '', 'stock': 0, 'sales': []})
        
        for ds in daily_sales:
            pid = ds['product_id']
            product_data[pid]['name'] = ds['product__name']
            product_data[pid]['stock'] = ds['product__stock']
            product_data[pid]['sales'].append(ds['daily_sold'])
            
        results = []
        lead_time = 7 # Asumimos 7 días para reabastecimiento (Lead Time)
        z_score = 1.65 # Nivel de servicio del 95%
        
        for pid, data in product_data.items():
            sales = data['sales']
            # Rellenar con 0s para los días sin ventas dentro de los 30 días
            while len(sales) < 30:
                sales.append(0)
                
            mean = sum(sales) / len(sales)
            variance = sum((x - mean) ** 2 for x in sales) / len(sales)
            std_dev = math.sqrt(variance)
            
            safety_stock = z_score * std_dev * math.sqrt(lead_time)
            reorder_point = (mean * lead_time) + safety_stock
            
            results.append({
                'product_name': data['name'],
                'current_stock': data['stock'],
                'mean_daily_sales': round(mean, 2),
                'safety_stock_recommended': math.ceil(safety_stock),
                'reorder_point': math.ceil(reorder_point),
                'status': 'CRITICAL' if data['stock'] <= math.ceil(reorder_point) else 'HEALTHY'
            })
            
        # Devolver primero los críticos
        results = sorted(results, key=lambda x: (x['status'] == 'HEALTHY', x['current_stock']))
        return Response(results)

class ABCAnalysisReport(APIView):
    """
    Análisis ABC (Principio de Pareto) para el control de Inventarios basado en el valor de ventas.
    A = Top 80% ingresos, B = Siguiente 15%, C = Último 5%
    """
    permission_classes = [IsAuthenticated, IsAdminRole]

    def get(self, request):
        products = SaleDetail.objects.filter(sale__store=request.user.store)\
            .values('product__name')\
            .annotate(total_revenue=Sum(F('quantity') * F('price_at_sale'), output_field=FloatField()))\
            .order_by('-total_revenue')
            
        total_store_revenue = sum(p['total_revenue'] for p in products)
        if total_store_revenue == 0:
            return Response([])
            
        cumulative_revenue = 0
        results = []
        
        for p in products:
            rev = p['total_revenue']
            cumulative_revenue += rev
            cumulative_percentage = (cumulative_revenue / total_store_revenue) * 100
            
            category = 'C'
            if cumulative_percentage <= 80:
                category = 'A'
            elif cumulative_percentage <= 95:
                category = 'B'
                
            results.append({
                'product_name': p['product__name'],
                'revenue': round(rev, 2),
                'category': category,
                'cumulative_percent': round(cumulative_percentage, 2)
            })
            
        return Response(results)
