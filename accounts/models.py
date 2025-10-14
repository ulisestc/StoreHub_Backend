from django.db import models
from django.contrib.auth.models import AbstractUser
from .managers import CustomUserManager

# Create your models here.
class User(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('seller', 'Vendedor'),
    )

    username = None
    email = models.EmailField('correo electrónico', unique=True)
    role = models.CharField("Rol", max_length=10, choices=ROLE_CHOICES, default='seller')
    first_name = models.CharField("Nombres", max_length=150)
    last_name = models.CharField("Apellidos", max_length=150)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'