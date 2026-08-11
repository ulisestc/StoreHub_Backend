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

class StoreProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    store_name = models.CharField("Nombre de la tienda", max_length=100)
    
    # Feature Flags
    is_premium = models.BooleanField("Premium Status", default=False) 
    
    # Límites de Cuota (Quotas)
    max_products = models.IntegerField("Límite de productos", default=50) # La tiendita gratis solo puede registrar 50 productos
    max_users = models.IntegerField("Límite de usuarios", default=2) # Solo dos cajeros en la versión gratis

    def __str__(self):
        return f"Perfil de {self.user.email} - {self.store_name}"

    class Meta:
        verbose_name = 'Perfil de Tienda'
        verbose_name_plural = 'Perfiles de Tienda'

from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        StoreProfile.objects.create(
            user=instance, 
            store_name=f"Tienda de {instance.first_name}" if instance.first_name else "Mi Tiendita"
        )

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()