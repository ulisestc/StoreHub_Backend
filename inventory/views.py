from django.shortcuts import render
from rest_framework import viewsets, mixins, serializers
from rest_framework.permissions import IsAuthenticated
from .models import InventoryMovement
from .serializers import InventoryMovementSerializer
from django.db import transaction
# Create your views here.
class InventoryMovementViewSet(
    mixins.ListModelMixin, #GET
    mixins.CreateModelMixin, #POST
    mixins.RetrieveModelMixin, #GET con ID
    viewsets.GenericViewSet
):
    queryset = InventoryMovement.objects.all().order_by('-timestamp')
    serializer_class = InventoryMovementSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):

        product = serializer.validated_data['product']
        quantity = serializer.validated_data['quantity']
        movement_type = serializer.validated_data['type']

        try: 
            with transaction.atomic():

                if movement_type == 'in':
                    product.stock += quantity
                elif movement_type == 'out':
                    product.stock -= quantity
                
                product.save()

                serializer.save(user=self.request.user)

        except Exception as e:
            raise serializers.ValidationError(f"Error al registrar el movimiento de inventario: {str(e)}")
