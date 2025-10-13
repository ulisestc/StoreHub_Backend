from django.db import models

# Create your models here.
class Client(models.Model):
    name = models.CharField(max_length=200)
    email = models.EmailField(unique=True, null = True, blank = True)
    phone = models.CharField(max_length=20, null = True, blank = True)