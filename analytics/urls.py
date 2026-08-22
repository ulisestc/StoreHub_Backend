from django.urls import path
from .views import (
    DashboardKPIView,
    SalesOverTimeView,
    TopProductsView,
    SalesByCategoryView,
    SalesByHourView,
    TopSellersView,
    ProfitabilityView,
    PeriodComparisonView,
    PremiumUpgradeView,
    DemandPredictionView,
    CancelPremiumView
)
from .chatbot import ChatbotView

urlpatterns = [
    path('analytics/dashboard/', DashboardKPIView.as_view(), name='analytics-dashboard'),
    path('analytics/sales-over-time/', SalesOverTimeView.as_view(), name='analytics-sales-over-time'),
    path('analytics/top-products/', TopProductsView.as_view(), name='analytics-top-products'),
    path('analytics/sales-by-category/', SalesByCategoryView.as_view(), name='analytics-sales-by-category'),
    path('analytics/sales-by-hour/', SalesByHourView.as_view(), name='analytics-sales-by-hour'),
    path('analytics/top-sellers/', TopSellersView.as_view(), name='analytics-top-sellers'),
    path('analytics/profitability/', ProfitabilityView.as_view(), name='analytics-profitability'),
    path('analytics/comparisons/', PeriodComparisonView.as_view(), name='analytics-comparisons'),
    path('analytics/predictions/', DemandPredictionView.as_view(), name='analytics-predictions'),
    path('analytics/chatbot/', ChatbotView.as_view(), name='analytics-chatbot'),
    path('analytics/store/upgrade/', PremiumUpgradeView.as_view(), name='premium-upgrade'),
    path('analytics/store/cancel-premium/', CancelPremiumView.as_view(), name='premium-cancel'),
]
