from rest_framework import serializers
from .models import InventoryMovement
from products.models import Product # Para validar

class InventoryMovementSerializer(serializers.ModelSerializer):

    product_name = serializers.CharField(source='product.name', read_only=True)
    
    class Meta: 
        model = InventoryMovement
        fields = [
            'id',
            'product',
            'product_name',
            'type',
            'quantity',
            'user',
            'timestamp'
        ]

        read_only_fields = ['timestamp', 'user', 'product_name'] #se asignan en la vista
