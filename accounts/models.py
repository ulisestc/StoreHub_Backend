from django.db import models
from django.contrib.auth.models import AbstractUser
from .managers import CustomUserManager
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db.utils import OperationalError, ProgrammingError
from django.db import transaction

class Store(models.Model):
    name = models.CharField("Nombre de la tienda", max_length=100)
    
    # Feature Flags y Estados
    is_premium = models.BooleanField("Premium Status", default=False) 
    is_setup_complete = models.BooleanField("Configuración completa", default=False)
    
    # Información Pública / Recibos
    address = models.CharField("Dirección", max_length=255, blank=True)
    phone = models.CharField("Teléfono", max_length=20, blank=True)
    email = models.EmailField("Correo de contacto", blank=True)
    receipt_message = models.TextField("Mensaje de ticket", blank=True, help_text="Mensaje que aparece al final de los tickets de compra.")

    # Límites de Cuota (Quotas)
    max_products = models.IntegerField("Límite de productos", default=50)
    max_users = models.IntegerField("Límite de usuarios", default=2)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Tienda'
        verbose_name_plural = 'Tiendas'

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
    must_change_password = models.BooleanField("Debe cambiar contraseña", default=False)
    
    # Multi-tenancy
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='users', null=True, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'

@receiver(post_save, sender=User)
def create_user_store(sender, instance, created, **kwargs):
    if created and instance.role == 'admin':
        try:
            with transaction.atomic():
                store = Store.objects.create(
                    name=f"Tienda de {instance.first_name}" if instance.first_name else "Mi Tiendita"
                )
                # Usar update() para no disparar recursivamente el post_save
                User.objects.filter(pk=instance.pk).update(store=store)
        except (OperationalError, ProgrammingError):
            pass