from django.db import models

class Client(models.Model):
    name = models.CharField(max_length=200)
    email = models.EmailField(null=True, blank=True) # Ya no puede ser unique=True a nivel global.
    phone = models.CharField(max_length=20, null=True, blank=True)
    store = models.ForeignKey('accounts.Store', on_delete=models.CASCADE, related_name='clients')

    class Meta:
        unique_together = (('store', 'email'),)