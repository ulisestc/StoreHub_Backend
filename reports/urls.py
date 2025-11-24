from django.urls import path
from .views import LowStockProductsReport, SalesByDateReport, TopProductsReport, reports

urlpatterns = [
    path('reports', reports, name='reports'),
    path('reports/sales-by-date/', SalesByDateReport, name='sales-by-date' ),
    path('reports/top-products/', TopProductsReport, name='top-products' ),
    path('reports/low-stock-products/', LowStockProductsReport, name='low-stock-products' ),
]