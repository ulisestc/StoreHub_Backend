from django.db.models import Sum, Count, Avg, F, Value, CharField
from django.db.models.functions import TruncDay, TruncWeek, TruncMonth, ExtractHour, Concat
from django.utils import timezone
from datetime import timedelta
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from accounts.permissions import IsAdminRole
from .permissions import IsPremiumStore
from sales.models import Sale, SaleDetail
from products.models import Product

class DashboardKPIView(APIView):
    permission_classes = [IsAuthenticated, IsAdminRole]

    def get(self, request):
        store = request.user.store
        today = timezone.localdate()
        first_day_of_month = today.replace(day=1)
        
        ventas_hoy = Sale.objects.filter(store=store, created_at__date=today)
        ventas_mes = Sale.objects.filter(store=store, created_at__date__gte=first_day_of_month)

        hoy_aggs = ventas_hoy.aggregate(
            count=Count('id'),
            sum_total=Sum('total'),
            avg_total=Avg('total')
        )
        # Separated to avoid multiplication due to JOINs in the aggregate above
        hoy_qty = ventas_hoy.aggregate(sum_qty=Sum('details__quantity'))['sum_qty']
        
        mes_aggs = ventas_mes.aggregate(
            count=Count('id'),
            sum_total=Sum('total')
        )
        
        return Response({
            "ventas_hoy": hoy_aggs['count'] or 0,
            "ingresos_hoy": hoy_aggs['sum_total'] or 0.0,
            "ticket_promedio": hoy_aggs['avg_total'] or 0.0,
            "productos_vendidos_hoy": hoy_qty or 0,
            "ingresos_mes": mes_aggs['sum_total'] or 0.0,
            "ventas_mes": mes_aggs['count'] or 0
        })

class SalesOverTimeView(APIView):
    permission_classes = [IsAuthenticated, IsAdminRole]

    def get(self, request):
        store = request.user.store
        period = request.query_params.get('period', 'day')
        days = int(request.query_params.get('days', 30))
        
        start_date = timezone.now() - timedelta(days=days)
        qs = Sale.objects.filter(store=store, created_at__gte=start_date)
        
        if period == 'week':
            trunc_func = TruncWeek('created_at')
        elif period == 'month':
            trunc_func = TruncMonth('created_at')
        else:
            trunc_func = TruncDay('created_at')
            
        sales = qs.annotate(date_trunc=trunc_func).values('date_trunc').annotate(
            total=Sum('total'),
            count=Count('id')
        ).order_by('date_trunc')
        
        return Response([
            {"date": item['date_trunc'].strftime('%Y-%m-%d'), "total": item['total'] or 0.0, "count": item['count'] or 0}
            for item in sales
        ])

class TopProductsView(APIView):
    permission_classes = [IsAuthenticated, IsAdminRole]

    def get(self, request):
        store = request.user.store
        limit = int(request.query_params.get('limit', 10))
        
        products = SaleDetail.objects.filter(sale__store=store).values(
            'product__name', 'product__id'
        ).annotate(
            total_vendido=Sum('quantity'),
            revenue=Sum(F('quantity') * F('price_at_sale'))
        ).order_by('-total_vendido')[:limit]
        
        return Response([
            {
                "product_name": item['product__name'],
                "product_id": item['product__id'],
                "total_vendido": item['total_vendido'] or 0,
                "revenue": item['revenue'] or 0.0
            }
            for item in products
        ])

class SalesByCategoryView(APIView):
    permission_classes = [IsAuthenticated, IsAdminRole]

    def get(self, request):
        store = request.user.store
        
        categories = SaleDetail.objects.filter(sale__store=store).values(
            'product__category__name'
        ).annotate(
            total=Sum(F('quantity') * F('price_at_sale')),
            count=Count('sale__id', distinct=True)
        ).order_by('-total')
        
        return Response([
            {
                "category": item['product__category__name'] or 'Sin Categoría',
                "total": item['total'] or 0.0,
                "count": item['count'] or 0
            }
            for item in categories
        ])

class SalesByHourView(APIView):
    permission_classes = [IsAuthenticated, IsAdminRole]

    def get(self, request):
        store = request.user.store
        
        sales_by_hour = Sale.objects.filter(store=store).annotate(
            hour=ExtractHour('created_at')
        ).values('hour').annotate(
            total=Sum('total'),
            count=Count('id')
        ).order_by('hour')
        
        return Response([
            {"hour": item['hour'], "total": item['total'] or 0.0, "count": item['count'] or 0}
            for item in sales_by_hour
        ])

class TopSellersView(APIView):
    permission_classes = [IsAuthenticated, IsAdminRole]

    def get(self, request):
        store = request.user.store
        
        sellers = Sale.objects.filter(store=store).annotate(
            seller_name=Concat('user__first_name', Value(' '), 'user__last_name', output_field=CharField())
        ).values('seller_name').annotate(
            ventas=Count('id'),
            monto=Sum('total')
        ).order_by('-ventas')
        
        return Response([
            {
                "seller": item['seller_name'].strip() or 'Desconocido',
                "ventas": item['ventas'] or 0,
                "monto": item['monto'] or 0.0
            }
            for item in sellers
        ])

class ProfitabilityView(APIView):
    permission_classes = [IsAuthenticated, IsAdminRole, IsPremiumStore]

    def get(self, request):
        store = request.user.store
        
        products = SaleDetail.objects.filter(sale__store=store).values(
            'product__name'
        ).annotate(
            revenue=Sum(F('quantity') * F('price_at_sale')),
            cost=Sum(F('quantity') * F('product__cost_price'))
        ).order_by('-revenue')
        
        results = []
        for item in products:
            revenue = item['revenue'] or 0
            cost = item['cost'] or 0
            profit = revenue - cost
            margin = (profit / revenue * 100) if revenue > 0 else 0
            
            results.append({
                "product_name": item['product__name'],
                "revenue": revenue,
                "cost": cost,
                "profit": profit,
                "margin": round(margin, 2)
            })
            
        return Response(results)

class PeriodComparisonView(APIView):
    permission_classes = [IsAuthenticated, IsAdminRole, IsPremiumStore]

    def get(self, request):
        store = request.user.store
        
        curr_start = request.query_params.get('current_start')
        curr_end = request.query_params.get('current_end')
        prev_start = request.query_params.get('previous_start')
        prev_end = request.query_params.get('previous_end')
        
        if not all([curr_start, curr_end, prev_start, prev_end]):
            return Response({"error": "Faltan fechas de comparación"}, status=400)
            
        curr_aggs = Sale.objects.filter(store=store, created_at__date__range=[curr_start, curr_end]).aggregate(
            total=Sum('total'),
            count=Count('id')
        )
        
        prev_aggs = Sale.objects.filter(store=store, created_at__date__range=[prev_start, prev_end]).aggregate(
            total=Sum('total'),
            count=Count('id')
        )
        
        curr_total = curr_aggs['total'] or 0.0
        prev_total = prev_aggs['total'] or 0.0
        curr_count = curr_aggs['count'] or 0
        prev_count = prev_aggs['count'] or 0
        
        change_percent = 0
        if prev_total > 0:
            change_percent = ((curr_total - prev_total) / prev_total) * 100
            
        return Response({
            "current": {"total": curr_total, "count": curr_count},
            "previous": {"total": prev_total, "count": prev_count},
            "change_percent": round(change_percent, 2)
        })

class PremiumUpgradeView(APIView):
    permission_classes = [IsAuthenticated, IsAdminRole]

    def post(self, request):
        store = request.user.store
        if not store:
            return Response({"error": "Usuario sin tienda asociada."}, status=400)
            
        store.is_premium = True
        store.save()
        return Response({"message": "¡Felicidades! Tu tienda ahora es Premium.", "is_premium": True})

class CancelPremiumView(APIView):
    permission_classes = [IsAuthenticated, IsAdminRole, IsPremiumStore]

    def post(self, request):
        store = request.user.store
        store.is_premium = False
        store.save()
        return Response({"message": "Tu suscripción Premium ha sido cancelada.", "is_premium": False})

class DemandPredictionView(APIView):
    permission_classes = [IsAuthenticated, IsAdminRole, IsPremiumStore]

    def get(self, request):
        store = request.user.store
        days = int(request.query_params.get('days', 30))
        
        start_date = timezone.now() - timedelta(days=days)
        # Sales grouped by day
        sales = Sale.objects.filter(store=store, created_at__gte=start_date)\
                            .annotate(date_trunc=TruncDay('created_at'))\
                            .values('date_trunc')\
                            .annotate(total=Sum('total'))\
                            .order_by('date_trunc')
                            
        # Simple Linear Regression (y = mx + b)
        x_vals = []
        y_vals = []
        for i, s in enumerate(sales):
            x_vals.append(i)
            y_vals.append(float(s['total'] or 0))
            
        if len(x_vals) < 2:
            # Fallback si no hay suficientes datos históricos
            return Response({
                "historical_trend": "neutral",
                "slope": 0,
                "predictions": [{"date": (timezone.now() + timedelta(days=i)).strftime('%Y-%m-%d'), "predicted_total": 0} for i in range(1, 8)]
            })
            
        N = len(x_vals)
        sum_x = sum(x_vals)
        sum_y = sum(y_vals)
        sum_xy = sum(x * y for x, y in zip(x_vals, y_vals))
        sum_x2 = sum(x * x for x in x_vals)
        
        denominator = (N * sum_x2 - sum_x ** 2)
        m = (N * sum_xy - sum_x * sum_y) / denominator if denominator != 0 else 0
        b = (sum_y - m * sum_x) / N
        
        # Predict next 7 days
        predictions = []
        last_date = sales[len(sales)-1]['date_trunc'].date()
        for i in range(1, 8):
            next_x = N - 1 + i
            pred_y = max(0, m * next_x + b) # No negative sales
            pred_date = last_date + timedelta(days=i)
            predictions.append({
                "date": pred_date.strftime('%Y-%m-%d'),
                "predicted_total": round(pred_y, 2)
            })
            
        return Response({
            "historical_trend": "positive" if m > 0 else ("negative" if m < 0 else "neutral"),
            "slope": round(m, 4),
            "predictions": predictions
        })
