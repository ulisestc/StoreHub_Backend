from rest_framework import serializers
from .models import Product, Category

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

class ProductSerializer(serializers.ModelSerializer):
    is_active = serializers.BooleanField(default=True) # para evitar que se ponga false automaticamente al crear y no tener que agregarlo ecxplicitamtne
    
    class Meta:
        model = Product
        fields = ['id', 'name', 'sku', 'price', 'stock', 'category', 'is_active', 'description', 'cost_price']