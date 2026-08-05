"""
URL configuration for storehub_backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from rest_framework.schemas import get_schema_view
from .views import health_check, swagger_ui

urlpatterns = [
    path('admin/', admin.site.urls),

    # Documentación OpenAPI interactiva y Health Check
    path('api/schema/', get_schema_view(
        title="StoreHub REST API",
        description="API REST de Gestión de Inventario, Ventas y Analítica Financiera para la FCC BUAP",
        version="1.0.0"
    ), name='openapi-schema'),
    path('api/docs/', swagger_ui, name='swagger-ui'),
    path('api/health/', health_check, name='health-check'),

    # Endpoints de negocio
    path('api/', include('products.urls')),# /products /categories
    path('api/', include('clients.urls')), # /clients
    path('api/', include('inventory.urls')), # /inventory
    path('api/', include('sales.urls')), # /sales
    path('api/', include('reports.urls')), # /reports

    # Endpoints de autenticación
    path('api/auth/', include('djoser.urls')), # DJOSER : Registro, login etc
    path('api/auth/', include('djoser.urls.jwt')), # JWT : Manejo de tokens
]

