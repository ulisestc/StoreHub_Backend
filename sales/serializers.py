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
            'subtotal',
            'impuestos',
            'total',
            'created_at',
            'details',
        ]
        read_only_fields = ['subtotal','impuestos','total', 'created_at', 'user', 'client_name']

from .models import CashRegisterSession

class CashRegisterSessionSerializer(serializers.ModelSerializer):
    opened_by_name = serializers.CharField(source='opened_by.get_full_name', read_only=True)
    closed_by_name = serializers.CharField(source='closed_by.get_full_name', read_only=True)

    class Meta:
        model = CashRegisterSession
        fields = [
            'id',
            'store',
            'opened_by',
            'opened_by_name',
            'closed_by',
            'closed_by_name',
            'opening_balance',
            'expected_closing_balance',
            'actual_closing_balance',
            'opened_at',
            'closed_at',
            'notes',
            'is_open',
            'discrepancy'
        ]
        read_only_fields = ['store', 'opened_by', 'closed_by', 'opened_at', 'closed_at', 'expected_closing_balance']
