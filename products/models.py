from django.db import models

class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    store = models.ForeignKey('accounts.Store', on_delete=models.CASCADE, related_name='categories')

class Product(models.Model):
    name = models.CharField(max_length=200)
    sku = models.CharField(max_length=50) # No puede ser unique globalmente si hay multiples tiendas, el unique_together lo resolvemos despues o lo dejamos sin unique db-level
    barcode = models.CharField("Código de Barras", max_length=100, blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    category = models.ForeignKey(Category, related_name='products', on_delete=models.SET_NULL, null=True)
    is_active = models.BooleanField(default=True)
    description = models.TextField(blank=True, null=True)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    store = models.ForeignKey('accounts.Store', on_delete=models.CASCADE, related_name='products')

    class Meta:
        unique_together = (('store', 'sku'), ('store', 'barcode'))