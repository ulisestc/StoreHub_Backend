from decimal import Decimal
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

    # Configuración Regional y Fiscal
    country = models.CharField("País", max_length=50, default='Colombia')
    currency_code = models.CharField("Código de Moneda", max_length=5, default='COP')
    currency_symbol = models.CharField("Símbolo de Moneda", max_length=5, default='$')
    tax_rate = models.DecimalField("Tasa de Impuesto", max_digits=5, decimal_places=4, default=Decimal('0.1900'))
    tax_name = models.CharField("Nombre del Impuesto", max_length=20, default='IVA')

    # Límites de Cuota (Quotas)
    max_products = models.IntegerField("Límite de productos", default=500)
    max_users = models.IntegerField("Límite de usuarios", default=4)

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


class AuditLog(models.Model):
    ACTION_CHOICES = (
        ('PRECIO_CAMBIADO', 'Cambio de Precio'),
        ('INVENTARIO_AJUSTADO', 'Ajuste de Inventario'),
        ('PRODUCTO_CREADO', 'Producto Creado'),
        ('PRODUCTO_ELIMINADO', 'Producto Eliminado'),
        ('GASTO_REGISTRADO', 'Gasto Registrado'),
        ('GASTO_ELIMINADO', 'Gasto Eliminado'),
        ('CAJA_ABIERTA', 'Apertura de Caja'),
        ('CAJA_CERRADA', 'Cierre de Caja'),
        ('CONFIG_CAMBIADA', 'Configuración Modificada'),
        ('USUARIO_CREADO', 'Empleado Registrado'),
        ('USUARIO_ELIMINADO', 'Empleado Eliminado'),
    )

    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='audit_logs')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_logs')
    user_name = models.CharField("Usuario", max_length=150)
    user_role = models.CharField("Rol", max_length=20, default='admin')
    action = models.CharField("Acción", max_length=40, choices=ACTION_CHOICES)
    entity = models.CharField("Entidad", max_length=60)
    entity_id = models.CharField("ID de Entidad", max_length=60, blank=True, default='')
    description = models.TextField("Descripción")
    before_data = models.JSONField("Datos Anteriores", null=True, blank=True)
    after_data = models.JSONField("Datos Nuevos", null=True, blank=True)
    ip_address = models.CharField("Dirección IP", max_length=45, blank=True, null=True)
    created_at = models.DateTimeField("Fecha", auto_now_add=True)

    class Meta:
        verbose_name = 'Registro de Auditoría'
        verbose_name_plural = 'Bitácora de Auditoría'
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.action}] {self.description}"


def get_client_ip(request):
    if not request:
        return None
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def log_audit_event(request, action, entity, entity_id, description, before_data=None, after_data=None):
    """
    Registra de manera segura e inmutable un evento en la bitácora de auditoría de la tienda.
    Nunca interrumpe el flujo principal en caso de excepción.
    """
    try:
        user = getattr(request, 'user', None)
        if not user or not user.is_authenticated or not getattr(user, 'store', None):
            return None
        full_name = f"{user.first_name} {user.last_name}".strip() or user.email
        return AuditLog.objects.create(
            store=user.store,
            user=user,
            user_name=full_name,
            user_role=getattr(user, 'role', 'seller'),
            action=action,
            entity=entity,
            entity_id=str(entity_id) if entity_id is not None else '',
            description=description,
            before_data=before_data,
            after_data=after_data,
            ip_address=get_client_ip(request),
        )
    except Exception:
        return None