from rest_framework import serializers
from .models import Expense

class ExpenseSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    category_display = serializers.CharField(source='get_category_display', read_only=True)

    class Meta:
        model = Expense
        fields = [
            'id',
            'store',
            'user',
            'user_name',
            'title',
            'category',
            'category_display',
            'amount',
            'date',
            'description',
            'created_at',
        ]
        read_only_fields = ['store', 'user', 'created_at']

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("El monto del gasto debe ser mayor a cero.")
        return value
