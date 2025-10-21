from django.urls import path
from .views import SalesByDateReport, TopProductsReport

urlpatterns = [
    path('reports/sales-by-date/', SalesByDateReport.as_view()),
    path('reports/top-products/', TopProductsReport.as_view()),
]