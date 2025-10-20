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

    def validate(self, data):

        if data['quantity'] <= 0:
            raise serializers.ValidationError("La cantidad debe ser un número positivo.")
        
        if data ['type'] == 'out':
            product = data ['product']
            quantity = data ['quantity']
            if product.stock < quantity:
                raise serializers.ValidationError("No hay suficiente stock para realizar esta salida.")
        return data