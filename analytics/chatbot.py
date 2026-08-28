from openai import OpenAI
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from accounts.permissions import IsAdminRole
from .permissions import IsPremiumStore
from sales.models import Sale, SaleDetail
from products.models import Product
from django.db.models import Sum, Count, Avg, F
from django.utils import timezone
from django.db import models
from datetime import timedelta
from reports.views import MarketBasketReport, SafetyStockReport, ABCAnalysisReport

class MockRequest:
    def __init__(self, store):
        self.user = type('MockUser', (), {'store': store})()

class ChatbotView(APIView):
    permission_classes = [IsAuthenticated, IsAdminRole, IsPremiumStore]

    def build_store_context(self, store):
        now = timezone.now()
        last_7_days = now - timedelta(days=7)
        last_30_days = now - timedelta(days=30)
        today = now.date()
        
        # Sales last 7 days
        sales_7d = Sale.objects.filter(store=store, created_at__gte=last_7_days).aggregate(
            count=Count('id'), total=Sum('total')
        )
        sales_7d_count = sales_7d['count'] or 0
        sales_7d_total = sales_7d['total'] or 0.0
        
        # Sales last 30 days
        sales_30d = Sale.objects.filter(store=store, created_at__gte=last_30_days)
        sales_30d_agg = sales_30d.aggregate(count=Count('id'), total=Sum('total'))
        sales_30d_count = sales_30d_agg['count'] or 0
        sales_30d_total = sales_30d_agg['total'] or 0.0
        
        # Nuevos KPIs
        atv = (sales_30d_total / sales_30d_count) if sales_30d_count > 0 else 0.0
        
        total_items_sold_30d = SaleDetail.objects.filter(sale__in=sales_30d).aggregate(total=Sum('quantity'))['total'] or 0
        upt = (total_items_sold_30d / sales_30d_count) if sales_30d_count > 0 else 0.0
        
        sales_with_client_30d = sales_30d.filter(client__isnull=False).count()
        loyalty_rate = (sales_with_client_30d / sales_30d_count * 100) if sales_30d_count > 0 else 0.0
        
        inventory_value_agg = Product.objects.filter(store=store, is_active=True).aggregate(
            val=Sum(F('stock') * F('cost_price'), output_field=models.DecimalField())
        )
        inventory_value = inventory_value_agg['val'] or 0.0
        
        # Sales today
        sales_today = Sale.objects.filter(store=store, created_at__date=today).aggregate(
            count=Count('id'), total=Sum('total')
        )
        sales_today_count = sales_today['count'] or 0
        sales_today_total = sales_today['total'] or 0.0
        
        # Top 5 products by quantity
        top_products = SaleDetail.objects.filter(sale__store=store, sale__created_at__gte=last_30_days).values(
            'product__name'
        ).annotate(total_qty=Sum('quantity')).order_by('-total_qty')[:5]
        top_products_list = ", ".join([f"{p['product__name']} ({p['total_qty']} ud)" for p in top_products])
        
        # Top 3 profitable products
        profitable_products = SaleDetail.objects.filter(sale__store=store, sale__created_at__gte=last_30_days).values(
            'product__name'
        ).annotate(
            profit=Sum((F('price_at_sale') - F('product__cost_price')) * F('quantity'))
        ).order_by('-profit')[:3]
        profit_products_list = ", ".join([f"{p['product__name']} (Ganancia: ${p['profit']})" for p in profitable_products])

        # Products with stock < 10
        low_stock = Product.objects.filter(store=store, stock__lt=10, is_active=True)
        low_stock_count = low_stock.count()
        low_stock_names = ", ".join([p.name for p in low_stock[:5]])
        
        # Active products & Clients
        active_products_count = Product.objects.filter(store=store, is_active=True).count()
        clients_count = store.clients.count() if hasattr(store, 'clients') else 0
        
        # Premium Features Data
        mock_req = MockRequest(store)
        
        # 1. Market Basket
        basket_data = MarketBasketReport().get(mock_req).data
        basket_str = "No hay datos de cesta de compra."
        if basket_data:
            basket_str = ", ".join([f"[{r['product_a']} + {r['product_b']} ({r['confidence_a_to_b']} %)]" for r in basket_data[:3]])
            
        # 2. Safety Stock
        safety_data = SafetyStockReport().get(mock_req).data
        critical_stock = [s for s in safety_data if s['status'] == 'CRITICAL']
        safety_str = "Inventario sano."
        if critical_stock:
            safety_str = ", ".join([f"{s['product_name']} (Stock: {s['current_stock']}, Min: {s['reorder_point']}, Faltan {(s['current_stock']/s['mean_daily_sales'] if s['mean_daily_sales'] > 0 else 0):.0f} días)" for s in critical_stock[:3]])
            
        # 3. ABC Analysis
        abc_data = ABCAnalysisReport().get(mock_req).data
        category_a = [a['product_name'] for a in abc_data if a['category'] == 'A']
        category_b = [b['product_name'] for b in abc_data if b['category'] == 'B']
        category_c = [c['product_name'] for c in abc_data if c['category'] == 'C']
        abc_str_a = ", ".join(category_a[:5]) if category_a else "N/A"
        abc_str_b = ", ".join(category_b[:5]) if category_b else "N/A"
        abc_str_c = ", ".join(category_c[:5]) if category_c else "N/A"
        
        context = (
            f"- **Tienda:** {store.name}\n"
            f"- **Capital Inmovilizado (Inventario):** ${inventory_value}\n"
            f"- **Métricas 30 días:** ATV (Ticket Promedio): ${atv:.2f}, UPT (Unidades/Transacción): {upt:.1f}, Tasa de Lealtad: {loyalty_rate:.1f}%\n"
            f"- **Ventas hoy:** {sales_today_count} ventas (${sales_today_total})\n"
            f"- **Ventas 7 días:** {sales_7d_count} ventas (${sales_7d_total})\n"
            f"- **Top 5 más vendidos (30 días):** {top_products_list}\n"
            f"- **Top 3 más rentables (30 días):** {profit_products_list}\n"
            f"- **Bajo stock (<10):** {low_stock_count} productos (ej. {low_stock_names})\n"
            f"- **Total de Productos / Clientes:** {active_products_count} / {clients_count}\n"
            f"\n**Métricas de Inteligencia Avanzada (Premium):**\n"
            f"- **Análisis ABC (Pareto):**\n"
            f"  * Categoría A (Top 80% ingresos - Prioridad máxima): {abc_str_a}\n"
            f"  * Categoría B (Siguiente 15% ingresos - Mantener): {abc_str_b}\n"
            f"  * Categoría C (Último 5% ingresos - Evaluar liquidar): {abc_str_c}\n"
            f"- **Alertas de Inventario Estadístico (CRÍTICOS):** {safety_str}\n"
            f"- **Cesta de Compra (Cross-Selling rules):** {basket_str}\n"
        )
        return context

    def post(self, request):
        if not settings.DEEPSEEK_API_KEY:
            return Response({"error": "DEEPSEEK_API_KEY no está configurada."}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            
        message = request.data.get('message')
        if not message:
            return Response({"error": "El campo 'message' es requerido."}, status=status.HTTP_400_BAD_REQUEST)
            
        store = request.user.store
        context_data = self.build_store_context(store)
        
        system_prompt = (
            f"Eres 'StoreHub AI', un Asesor Financiero y Analista de Crédito (Alternative Credit Scoring) para la tienda '{store.name}'. "
            "Tu misión es ayudar al dueño a formalizarse, maximizar sus ganancias, demostrar su capacidad crediticia y optimizar su inventario basado en datos. "
            "Habla con un tono profesional, experto pero alentador (como un consultor financiero de Silicon Valley y experto en Fintech). "
            "**REGLA CRÍTICA:** Siempre formatea tus respuestas utilizando Markdown (usa negritas, listas con viñetas `*` y tablas si es necesario) para que sea visualmente impecable. "
            "Analiza los siguientes datos financieros y operativos reales para dar tus recomendaciones (incluyendo ATV, UPT, Capital Inmovilizado y Tasa de Lealtad). Si te preguntan algo fuera del negocio, amablemente redirige la conversación al rendimiento de la tienda o a temas financieros.\n\n"
            f"**Datos actuales del negocio:**\n{context_data}"
        )
        
        client = OpenAI(
            api_key=settings.DEEPSEEK_API_KEY,
            base_url=settings.DEEPSEEK_BASE_URL
        )
        
        try:
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ]
            )
            reply = response.choices[0].message.content
            return Response({"reply": reply})
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
