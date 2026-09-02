from django.db import models

# Create your models here.
class InventoryMovement(models.Model):
    MOVEMENT_TYPES = (('in', 'Entrada'), ('out', 'Salida'), ('loss', 'Pérdida'))
    product = models.ForeignKey('products.Product', on_delete= models.CASCADE)
    type = models.CharField(max_length=4, choices=MOVEMENT_TYPES)
    quantity = models.PositiveIntegerField()
    user = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)