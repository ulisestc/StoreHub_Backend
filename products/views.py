from rest_framework import viewsets
from .models import Product, Category
from .serializers import ProductSerializer, CategorySerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import SearchFilter
from django_filters.rest_framework import DjangoFilterBackend

class CategoryViewSet(viewsets.ModelViewSet):
    serializer_class = CategorySerializer
    permission_classes =  [IsAuthenticated]

    def get_queryset(self):
        # Filtrar por la tienda del usuario
        return Category.objects.filter(store=self.request.user.store)

    def perform_create(self, serializer):
        # Inyectar la tienda del usuario al crear
        serializer.save(store=self.request.user.store)

class ProductViewSet(viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    permission_classes =  [IsAuthenticated]

    filter_backends = [SearchFilter, DjangoFilterBackend]
    search_fields = ['name', 'sku']
    filterset_fields = ['category']

    def get_queryset(self):
        return Product.objects.filter(store=self.request.user.store)

    def perform_create(self, serializer):
        from django.db import IntegrityError
        from rest_framework.exceptions import ValidationError
        try:
            serializer.save(store=self.request.user.store)
        except IntegrityError:
            raise ValidationError({'non_field_errors': ['Ya existe un producto con este código de barras o SKU en tu tienda.']})