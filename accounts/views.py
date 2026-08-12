from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied, ValidationError
from django.contrib.auth import get_user_model
from django.conf import settings
from djoser.email import ActivationEmail
from djoser import utils

from .serializers import EmployeeSerializer

User = get_user_model()

class EmployeeViewSet(viewsets.ModelViewSet):
    serializer_class = EmployeeSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.role != 'admin':
            return User.objects.none()
        return User.objects.filter(store=self.request.user.store, role='seller')

    def perform_create(self, serializer):
        if self.request.user.role != 'admin':
            raise PermissionDenied("Solo los administradores pueden crear empleados.")
            
        store = self.request.user.store
        current_employees = User.objects.filter(store=store).count()
        if not store.is_premium and current_employees >= store.max_users:
            raise ValidationError({'non_field_errors': ["Has alcanzado el límite de usuarios de tu plan gratuito. Mejora a Premium para agregar más."]})
            
        # Crear usuario como inactivo para que Djoser mande el correo de activación
        user = serializer.save(store=store, role='seller', is_active=False)
        
        # Enviar correo de activación de Djoser
        if settings.DJOSER.get('SEND_ACTIVATION_EMAIL'):
            context = {"user": user}
            to = [user.email]
            ActivationEmail(self.request, context).send(to)

    def perform_destroy(self, instance):
        if self.request.user.role != 'admin':
            raise PermissionDenied("Solo los administradores pueden desactivar empleados.")
        
        # En lugar de eliminar, desactivamos
        instance.is_active = False
        instance.save()
