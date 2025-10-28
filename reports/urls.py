from django.urls import path
from .views import LowStockProductsReport, SalesByDateReport, TopProductsReport

urlpatterns = [
    path('reports/sales-by-date/', SalesByDateReport.as_view()),
    path('reports/top-products/', TopProductsReport.as_view()),
    path('reports/low-stock-products/', LowStockProductsReport.as_view()),
]