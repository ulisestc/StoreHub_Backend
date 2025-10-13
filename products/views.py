from rest_framework import viewsets
from .models import Product, Category
from .serializers import ProductSerializer, CategorySerializer
from django.shortcuts import render

# Create your views here.
class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    