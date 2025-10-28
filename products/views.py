from rest_framework import viewsets
from .models import Product, Category
from .serializers import ProductSerializer, CategorySerializer
from django.shortcuts import render
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import SearchFilter

# Create your views here.
class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes =  [IsAuthenticated] # Para no poder modificar sin ser usuario

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes =  [IsAuthenticated] # Para no poder modificar sin ser usuario

    filter_backends = [SearchFilter]
    search_fields = ['name', 'sku']  # parametro ?search=X
    filterset_fields = ['category']  # parametro ?category=X
    