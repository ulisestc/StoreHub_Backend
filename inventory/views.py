from django.shortcuts import render
from rest_framework import viewsets, mixins, serializers
from rest_framework.permissions import IsAuthenticated
from .models import InventoryMovement
from .serializers import InventoryMovementSerializer
from django.db import transaction
from accounts.permissions import IsAdminRole

# Create your views here.
class InventoryMovementViewSet(
    mixins.ListModelMixin, #GET
    mixins.CreateModelMixin, #POST
    mixins.RetrieveModelMixin, #GET con ID
    viewsets.GenericViewSet
):
    def get_queryset(self):
        return InventoryMovement.objects.filter(product__store=self.request.user.store).order_by('-timestamp')
    serializer_class = InventoryMovementSerializer
    permission_classes = [IsAuthenticated, IsAdminRole]

    def perform_create(self, serializer):

        product = serializer.validated_data['product']
        quantity = serializer.validated_data['quantity']
        movement_type = serializer.validated_data['type']

        try: 
            with transaction.atomic():
                
                # Validaciones, no se puede usar negativos en quantity
                if quantity <= 0:
                    raise serializers.ValidationError("La cantidad debe ser mayor a cero.")
                # No se puede sacar más de lo que hay en stock
                if movement_type == 'out' and product.stock < quantity:
                    raise serializers.ValidationError("No hay suficiente stock para realizar esta salida.")
                # operaciones
                if movement_type == 'in':
                    product.stock += quantity
                elif movement_type in ['out', 'loss']:
                    product.stock -= quantity
                
                product.save()

                serializer.save(user=self.request.user)

        except Exception as e:
            raise serializers.ValidationError(f"Error al registrar el movimiento de inventario: {str(e)}")
