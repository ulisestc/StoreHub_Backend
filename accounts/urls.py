from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EmployeeViewSet, StoreConfigView, ForceChangePasswordView

router = DefaultRouter()
router.register(r'employees', EmployeeViewSet, basename='employee')

urlpatterns = [
    path('store/me/', StoreConfigView.as_view(), name='store-config'),
    path('auth/users/force_change_password/', ForceChangePasswordView.as_view(), name='force-change-password'),
    path('', include(router.urls)),
]
