from django.urls import path
from .views import (
    SalesByDateReport, TopProductsReport, LowStockProductsReport,
    InventoryValueReport, SalesHeatmapReport,
    MarketBasketReport, SafetyStockReport, ABCAnalysisReport
)

urlpatterns = [
    path('reports/sales-by-date/', SalesByDateReport.as_view(), name='sales-by-date'),
    path('reports/top-products/', TopProductsReport.as_view(), name='top-products'),
    path('reports/low-stock/', LowStockProductsReport.as_view(), name='low-stock'),
    path('reports/inventory-value/', InventoryValueReport.as_view(), name='inventory-value'),
    path('reports/sales-heatmap/', SalesHeatmapReport.as_view(), name='sales-heatmap'),
    path('analytics/market-basket/', MarketBasketReport.as_view(), name='market-basket'),
    path('analytics/safety-stock/', SafetyStockReport.as_view(), name='safety-stock'),
    path('analytics/abc-analysis/', ABCAnalysisReport.as_view(), name='abc-analysis'),
]