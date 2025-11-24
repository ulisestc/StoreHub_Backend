from django.urls import path
from .views import LowStockProductsReport, SalesByDateReport, TopProductsReport, reports

urlpatterns = [
    path('reports', reports.as_view(), name='reports'),
    path('reports/sales-by-date/', SalesByDateReport.as_view(), name='sales-by-date' ),
    path('reports/top-products/', TopProductsReport.as_view(), name='top-products' ),
    path('reports/low-stock-products/', LowStockProductsReport.as_view(), name='low-stock-products' ),
]