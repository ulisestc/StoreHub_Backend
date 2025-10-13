from django.contrib.auth.models import AbstractUser
from django.db import models

# Create your models here.
class User(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('seller', 'Vendedor'),
    )

    username = None
    email = models.EmailField('correo electrónico', unique=True)
    role = models.CharField("Rol", max_length=10, choices=ROLE_CHOICES, default='seller')

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []