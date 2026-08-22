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
from datetime import timedelta
from decimal import Decimal

class ChatbotView(APIView):
    permission_classes = [IsAuthenticated, IsAdminRole, IsPremiumStore]

    def build_store_context(self, store):
        now = timezone.now()
        last_7_days = now - timedelta(days=7)
        today = now.date()
        
        # Sales last 7 days
        sales_7d = Sale.objects.filter(store=store, created_at__gte=last_7_days).aggregate(
            count=Count('id'), total=Sum('total')
        )
        sales_7d_count = sales_7d['count'] or 0
        sales_7d_total = sales_7d['total'] or 0.0
        
        # Sales today
        sales_today = Sale.objects.filter(store=store, created_at__date=today).aggregate(
            count=Count('id'), total=Sum('total')
        )
        sales_today_count = sales_today['count'] or 0
        sales_today_total = sales_today['total'] or 0.0
        
        # Top 5 products last 30 days
        last_30_days = now - timedelta(days=30)
        top_products = SaleDetail.objects.filter(sale__store=store, sale__created_at__gte=last_30_days).values(
            'product__name'
        ).annotate(total_qty=Sum('quantity')).order_by('-total_qty')[:5]
        top_products_list = ", ".join([f"{p['product__name']} ({p['total_qty']} ud)" for p in top_products])
        
        # Products with stock < 10
        low_stock_count = Product.objects.filter(store=store, stock__lt=10, is_active=True).count()
        
        # Active products
        active_products_count = Product.objects.filter(store=store, is_active=True).count()
        
        # Clients
        clients_count = store.clients.count() if hasattr(store, 'clients') else 0 # Assuming related_name is clients
        
        context = (
            f"Tienda: {store.name}\n"
            f"Ventas hoy: {sales_today_count} ventas por un total de ${sales_today_total}\n"
            f"Ventas últimos 7 días: {sales_7d_count} ventas por un total de ${sales_7d_total}\n"
            f"Top 5 productos (30 días): {top_products_list}\n"
            f"Productos con bajo stock (<10): {low_stock_count}\n"
            f"Productos activos: {active_products_count}\n"
            f"Número de clientes: {clients_count}\n"
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
        
        system_prompt = f"Eres un asistente de negocios inteligente para la tienda '{store.name}'. Tu trabajo es ayudar al dueño a tomar decisiones basadas en datos. Responde de manera concisa, profesional y amigable. Usa los datos proporcionados para dar respuestas precisas. Si no tienes suficiente información, dilo honestamente. No inventes datos.\n\nDatos actuales:\n{context_data}"
        
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
