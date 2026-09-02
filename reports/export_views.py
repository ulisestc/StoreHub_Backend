import io
import datetime
from datetime import timedelta
import pandas as pd
from django.db.models import Count, F, FloatField, Sum
from django.http import HttpResponse
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from accounts.permissions import IsAdminRole
from products.models import Product
from sales.models import Sale, SaleDetail


class ExportFullReportToExcel(APIView):
    permission_classes = [IsAuthenticated, IsAdminRole]

    def get(self, request):
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        # Date range filtering logic
        if start_date and end_date:
            try:
                if isinstance(start_date, str) and len(start_date) == 10:
                    start_dt = datetime.datetime.strptime(f"{start_date} 00:00:00", "%Y-%m-%d %H:%M:%S")
                    start_date = timezone.make_aware(start_dt)
                if isinstance(end_date, str) and len(end_date) == 10:
                    end_dt = datetime.datetime.strptime(f"{end_date} 23:59:59", "%Y-%m-%d %H:%M:%S")
                    end_date = timezone.make_aware(end_dt)
            except ValueError:
                pass
                
            sales_qs = Sale.objects.filter(
                store=request.user.store,
                created_at__range=[start_date, end_date]
            ).select_related('user', 'client').order_by('-created_at')
            kpi_sales = sales_qs
        else:
            sales_qs = Sale.objects.filter(
                store=request.user.store
            ).select_related('user', 'client').order_by('-created_at')

            end_kpi = timezone.now()
            start_kpi = end_kpi - timedelta(days=30)
            kpi_sales = Sale.objects.filter(
                store=request.user.store,
                created_at__range=[start_kpi, end_kpi]
            )

        # 1. Sheet: Ventas
        sales_data = []
        for sale in sales_qs:
            vendedor = f"{sale.user.first_name} {sale.user.last_name}" if sale.user else 'Sistema'
            cliente = sale.client.name if sale.client else 'Público General'
            sales_data.append({
                'ID Venta': sale.id,
                'Fecha': sale.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'Vendedor': vendedor,
                'Cliente': cliente,
                'Subtotal': float(sale.subtotal),
                'Impuestos': float(sale.impuestos),
                'Total': float(sale.total),
            })
        df_sales = pd.DataFrame(sales_data)
        if df_sales.empty:
            df_sales = pd.DataFrame(columns=[
                'ID Venta', 'Fecha', 'Vendedor', 'Cliente', 'Subtotal', 'Impuestos', 'Total'
            ])

        # 2. Sheet: Detalle de Ventas
        details_qs = SaleDetail.objects.filter(
            sale__in=sales_qs
        ).select_related('sale', 'product').order_by('-sale__created_at')

        details_data = []
        for detail in details_qs:
            details_data.append({
                'ID Venta': detail.sale.id,
                'Fecha': detail.sale.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'Producto': detail.product.name if detail.product else 'N/A',
                'Cantidad': detail.quantity,
                'Precio Unitario': float(detail.price_at_sale),
                'Subtotal Línea': float(detail.quantity * detail.price_at_sale),
            })
        df_details = pd.DataFrame(details_data)
        if df_details.empty:
            df_details = pd.DataFrame(columns=[
                'ID Venta', 'Fecha', 'Producto', 'Cantidad', 'Precio Unitario', 'Subtotal Línea'
            ])

        # 3. Sheet: Inventario
        products_qs = Product.objects.filter(
            store=request.user.store,
            is_active=True
        ).select_related('category').order_by('name')

        inv_data = []
        for p in products_qs:
            margin = round(float((p.price - p.cost_price) / p.price * 100), 2) if p.price > 0 else 0.0
            inv_data.append({
                'SKU': p.sku or '',
                'Nombre': p.name,
                'Categoría': p.category.name if p.category else 'Sin Categoría',
                'Precio de Costo': float(p.cost_price),
                'Precio de Venta': float(p.price),
                'Margen (%)': margin,
                'Stock Actual': p.stock,
                'Valor en Inventario': float(p.stock * p.cost_price),
            })
        df_inv = pd.DataFrame(inv_data)
        if df_inv.empty:
            df_inv = pd.DataFrame(columns=[
                'SKU', 'Nombre', 'Categoría', 'Precio de Costo', 'Precio de Venta',
                'Margen (%)', 'Stock Actual', 'Valor en Inventario'
            ])

        # 4. Sheet: KPIs Financieros
        report = kpi_sales.aggregate(
            total_ventas=Sum('total'),
            num_transacciones=Count('id')
        )
        total_ventas = float(report['total_ventas'] or 0.0)
        num_transacciones = report['num_transacciones'] or 0

        atv = (total_ventas / num_transacciones) if num_transacciones > 0 else 0.0

        total_items = SaleDetail.objects.filter(sale__in=kpi_sales).aggregate(
            total=Sum('quantity')
        )['total'] or 0
        upt = (total_items / num_transacciones) if num_transacciones > 0 else 0.0

        sales_with_client = kpi_sales.filter(client__isnull=False).count()
        loyalty_rate = (sales_with_client / num_transacciones * 100) if num_transacciones > 0 else 0.0

        val = Product.objects.filter(store=request.user.store, is_active=True).aggregate(
            total_value=Sum(F('stock') * F('cost_price'), output_field=FloatField())
        )
        capital = float(val['total_value'] or 0.0)

        kpi_data = [
            {'Métrica': 'Total Ventas (Periodo)', 'Valor': float(round(total_ventas, 2))},
            {'Métrica': 'Transacciones', 'Valor': num_transacciones},
            {'Métrica': 'Ticket Promedio (ATV)', 'Valor': float(round(atv, 2))},
            {'Métrica': 'Unidades por Transacción (UPT)', 'Valor': float(round(upt, 2))},
            {'Métrica': 'Tasa de Lealtad (%)', 'Valor': float(round(loyalty_rate, 2))},
            {'Métrica': 'Capital Inmovilizado', 'Valor': float(round(capital, 2))},
        ]
        df_kpis = pd.DataFrame(kpi_data)
        if df_kpis.empty:
            df_kpis = pd.DataFrame(columns=['Métrica', 'Valor'])

        # Generar archivo Excel con 4 hojas usando ExcelWriter
        excel_file = io.BytesIO()
        with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
            df_sales.to_excel(writer, index=False, sheet_name='Ventas')
            df_details.to_excel(writer, index=False, sheet_name='Detalle de Ventas')
            df_inv.to_excel(writer, index=False, sheet_name='Inventario')
            df_kpis.to_excel(writer, index=False, sheet_name='KPIs Financieros')

        excel_file.seek(0)

        response = HttpResponse(
            excel_file.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename="reporte_storehub.xlsx"'
        return response
