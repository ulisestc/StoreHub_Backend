from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from .views import health_check

urlpatterns = [
    path('admin/', admin.site.urls),

    # Documentación automatizada de API (drf-spectacular) estilo exuth.uth.edu.mx
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    path('api/health/', health_check, name='health-check'),

    # Endpoints de negocio
    path('api/', include('products.urls')), # /products /categories
    path('api/', include('clients.urls')),  # /clients
    path('api/', include('inventory.urls')),# /inventory
    path('api/', include('sales.urls')),    # /sales
    path('api/', include('reports.urls')),  # /reports

    # Endpoints de autenticación
    path('api/auth/', include('djoser.urls')), # DJOSER : Registro, login etc
    path('api/auth/', include('djoser.urls.jwt')), # JWT : Manejo de tokens
]
