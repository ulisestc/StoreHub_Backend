from django.db import models
from django.utils import timezone

class Expense(models.Model):
    CATEGORY_CHOICES = (
        ('services', 'Servicios Públicos (Luz, Agua, Internet)'),
        ('rent', 'Arriendo / Renta'),
        ('payroll', 'Nómina / Sueldos'),
        ('supplies', 'Insumos y Empaques'),
        ('maintenance', 'Mantenimiento y Aseo'),
        ('transport', 'Transporte y Fletes'),
        ('taxes', 'Impuestos y Trámites'),
        ('other', 'Otros Gastos Operativos'),
    )

    store = models.ForeignKey('accounts.Store', on_delete=models.CASCADE, related_name='expenses')
    user = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, related_name='registered_expenses')
    title = models.CharField("Concepto", max_length=200)
    category = models.CharField("Categoría", max_length=30, choices=CATEGORY_CHOICES, default='other')
    amount = models.DecimalField("Monto", max_digits=12, decimal_places=2)
    date = models.DateField("Fecha del Gasto", default=timezone.localdate)
    description = models.TextField("Descripción / Notas", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Gasto Operativo'
        verbose_name_plural = 'Gastos Operativos'
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"{self.title} - ${self.amount} ({self.date})"
