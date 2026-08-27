from django.urls import path
from .views import (
    LowStockProductsReport, 
    SalesByDateReport, 
    TopProductsReport, 
    InventoryValueReport,
    SalesHeatmapReport
)

urlpatterns = [
    path('reports/sales-by-date/', SalesByDateReport.as_view(), name='sales-by-date' ),
    path('reports/top-products/', TopProductsReport.as_view(), name='top-products' ),
    path('reports/low-stock-products/', LowStockProductsReport.as_view(), name='low-stock-products' ),
    path('reports/inventory-value/', InventoryValueReport.as_view(), name='inventory-value' ),
    path('reports/sales-heatmap/', SalesHeatmapReport.as_view(), name='sales-heatmap' ),
]