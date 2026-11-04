from rest_framework import viewsets
from .models import Product, Category
from .serializers import ProductSerializer, CategorySerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import SearchFilter
from django_filters.rest_framework import DjangoFilterBackend

class CategoryViewSet(viewsets.ModelViewSet):
    serializer_class = CategorySerializer
    permission_classes =  [IsAuthenticated]

    def get_queryset(self):
        # Filtrar por la tienda del usuario
        return Category.objects.filter(store=self.request.user.store)

    def perform_create(self, serializer):
        # Inyectar la tienda del usuario al crear
        serializer.save(store=self.request.user.store)

class ProductViewSet(viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    permission_classes =  [IsAuthenticated]

    filter_backends = [SearchFilter, DjangoFilterBackend]
    search_fields = ['name', 'sku']
    filterset_fields = ['category']

    def get_queryset(self):
        return Product.objects.filter(store=self.request.user.store)

    def perform_create(self, serializer):
        from django.db import IntegrityError
        from rest_framework.exceptions import ValidationError
        from accounts.models import log_audit_event
        try:
            product = serializer.save(store=self.request.user.store)
            log_audit_event(
                request=self.request,
                action='PRODUCTO_CREADO',
                entity=product.name,
                entity_id=product.id,
                description=f"Registró nuevo producto '{product.name}' con precio ${float(product.price):.2f} y stock inicial de {product.stock} uds.",
                before_data=None,
                after_data={
                    'precio': float(product.price),
                    'costo': float(product.cost_price),
                    'stock': product.stock,
                    'sku': product.sku or ''
                }
            )
        except IntegrityError:
            raise ValidationError({'non_field_errors': ['Ya existe un producto con este código de barras o SKU en tu tienda.']})

    def perform_update(self, serializer):
        from django.db import IntegrityError
        from rest_framework.exceptions import ValidationError
        from accounts.models import log_audit_event

        instance = self.get_object()
        old_price = float(instance.price)
        old_cost = float(instance.cost_price)
        old_stock = instance.stock
        old_name = instance.name

        try:
            product = serializer.save()
        except IntegrityError:
            raise ValidationError({'non_field_errors': ['Ya existe un producto con este código de barras o SKU en tu tienda.']})

        new_price = float(product.price)
        new_cost = float(product.cost_price)
        new_stock = product.stock

        if abs(old_price - new_price) >= 0.01 or abs(old_cost - new_cost) >= 0.01:
            changes = []
            if abs(old_price - new_price) >= 0.01:
                changes.append(f"precio de venta de ${old_price:.2f} a ${new_price:.2f}")
            if abs(old_cost - new_cost) >= 0.01:
                changes.append(f"costo de ${old_cost:.2f} a ${new_cost:.2f}")
            log_audit_event(
                request=self.request,
                action='PRECIO_CAMBIADO',
                entity=product.name,
                entity_id=product.id,
                description=f"Actualizó {', '.join(changes)} en '{product.name}'",
                before_data={'precio': old_price, 'costo': old_cost},
                after_data={'precio': new_price, 'costo': new_cost}
            )

        if old_stock != new_stock:
            diff = new_stock - old_stock
            log_audit_event(
                request=self.request,
                action='INVENTARIO_AJUSTADO',
                entity=product.name,
                entity_id=product.id,
                description=f"Ajustó stock manual de '{product.name}' de {old_stock} a {new_stock} uds. ({diff:+d})",
                before_data={'stock': old_stock},
                after_data={'stock': new_stock, 'diferencia': diff}
            )

    def perform_destroy(self, instance):
        from accounts.models import log_audit_event
        log_audit_event(
            request=self.request,
            action='PRODUCTO_ELIMINADO',
            entity=instance.name,
            entity_id=instance.id,
            description=f"Eliminó el producto '{instance.name}' (stock restante: {instance.stock} uds., precio: ${float(instance.price):.2f})",
            before_data={'nombre': instance.name, 'precio': float(instance.price), 'stock': instance.stock, 'sku': instance.sku or ''},
            after_data=None
        )
        instance.delete()