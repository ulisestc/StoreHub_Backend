from rest_framework import serializers
from .models import Sale, SaleDetail
from clients.models import Client

class SaleDetailSerializer(serializers.ModelSerializer):
    #importamos nombre del producto para detalles
    product_name = serializers.CharField(source = 'product.name', read_only=True ) #read only para no tener que ponerlo en el POST

    class Meta:
        model = SaleDetail
        fields = [
            'id',
            'product',
            'product_name',
            'quantity',
            'price_at_sale',
        ]
        read_only_fields = ['price_at_sale', 'product_name']

        def validate(self, data):
            product = data ['product']
            quantity = data ['quantity']

            if quantity <= 0:
                raise serializers.ValidationError("La cantidad debe ser mayor a cero.")
            
            if product.stock < quantity:
                raise serializers.ValidationError("No hay suficiente stock para el producto seleccionado.")
            
            return data
        
class SaleSerializer(serializers.ModelSerializer):
    
    client_name = serializers.CharField(source = 'client.name', read_only=True)
    details = SaleDetailSerializer(many=True) #para agregar cada producto vendido
    user = serializers.StringRelatedField(read_only=True) #para mostrar el nombre del usuario que hizo la venta
    client = serializers.PrimaryKeyRelatedField(
        queryset=Client.objects.all(),
        allow_null=True,
        required=False
    ) #para seleccionar el cliente por su PK

    class Meta:
        model = Sale 
        fields = [
            'id',
            'user',
            'client',
            'client_name',
            'total',
            'created_at',
            'details',
        ]
        read_only_fields = ['total', 'created_at', 'user', 'client_name']

    def validate(self, details):
        if not details:
            raise serializers.ValidationError("La venta debe tener al menos un detalle.")
        return details
