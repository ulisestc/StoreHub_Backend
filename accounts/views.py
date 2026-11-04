from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied, ValidationError
from django.contrib.auth import get_user_model
from django.conf import settings
from djoser.email import ActivationEmail
from djoser import utils

from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from .serializers import EmployeeSerializer, StoreSerializer, AuditLogSerializer
from .models import AuditLog, log_audit_event
from .permissions import IsAdminRole
from rest_framework import mixins, filters

User = get_user_model()

class StoreConfigView(RetrieveUpdateAPIView):
    serializer_class = StoreSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        if self.request.user.role != 'admin':
            raise PermissionDenied("Solo los administradores pueden editar la configuración de la tienda.")
        return self.request.user.store

    def perform_update(self, serializer):
        store = self.get_object()
        old_data = {
            'nombre': store.name,
            'moneda': store.currency_code,
            'impuesto': f"{float(store.tax_rate) * 100:.1f}%",
            'telefono': store.phone or ''
        }
        updated_store = serializer.save()
        new_data = {
            'nombre': updated_store.name,
            'moneda': updated_store.currency_code,
            'impuesto': f"{float(updated_store.tax_rate) * 100:.1f}%",
            'telefono': updated_store.phone or ''
        }
        log_audit_event(
            request=self.request,
            action='CONFIG_CAMBIADA',
            entity=updated_store.name,
            entity_id=updated_store.id,
            description=f"Actualizó la configuración fiscal y operativa de la tienda '{updated_store.name}'",
            before_data=old_data,
            after_data=new_data
        )

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
            
        # Crear usuario activo con contraseña temporal
        temp_password = User.objects.make_random_password(length=8)
        user = serializer.save(store=store, role='seller', is_active=True, must_change_password=True)
        user.set_password(temp_password)
        user.save()

        log_audit_event(
            request=self.request,
            action='USUARIO_CREADO',
            entity=f"{user.first_name} {user.last_name}".strip() or user.email,
            entity_id=user.id,
            description=f"Dio de alta al vendedor '{user.first_name} {user.last_name}' ({user.email})",
            before_data=None,
            after_data={'email': user.email, 'rol': 'Vendedor'}
        )
        
        # Enviar correo con credenciales
        subject = 'Bienvenido a StoreHub'
        login_url = settings.DOMAIN if settings.DOMAIN.startswith('http') else f"http://{settings.DOMAIN}"

        context = {
            'first_name': user.first_name,
            'store_name': store.name,
            'login_url': login_url,
            'temp_password': temp_password,
        }
        
        html_message = render_to_string('email/invitation.html', context)
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject='Bienvenido a StoreHub',
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
            html_message=html_message,
        )

    def perform_destroy(self, instance):
        if self.request.user.role != 'admin':
            raise PermissionDenied("Solo los administradores pueden desactivar empleados.")
        
        emp_name = f"{instance.first_name} {instance.last_name}".strip() or instance.email
        log_audit_event(
            request=self.request,
            action='USUARIO_ELIMINADO',
            entity=emp_name,
            entity_id=instance.id,
            description=f"Revocó acceso y eliminó al vendedor '{emp_name}' ({instance.email})",
            before_data={'email': instance.email, 'nombre': emp_name},
            after_data=None
        )
        # Borramos el usuario de la base de datos para liberar cupo
        instance.delete()


class AuditLogViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """
    Bitácora inmutable de auditoría de seguridad (Solo lectura, exclusiva para Administradores).
    """
    serializer_class = AuditLogSerializer
    permission_classes = [IsAuthenticated, IsAdminRole]
    filter_backends = [filters.SearchFilter]
    search_fields = ['description', 'user_name', 'entity']

    def get_queryset(self):
        qs = AuditLog.objects.filter(store=self.request.user.store).order_by('-created_at')
        action_param = self.request.query_params.get('action')
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')

        if action_param:
            qs = qs.filter(action=action_param)
        if start_date:
            qs = qs.filter(created_at__date__gte=start_date)
        if end_date:
            qs = qs.filter(created_at__date__lte=end_date)

        return qs


class ForceChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        new_password = request.data.get('new_password')
        re_new_password = request.data.get('re_new_password')
        current_password = request.data.get('current_password')

        if not new_password or not re_new_password or not current_password:
            return Response({'error': 'Todos los campos son obligatorios.'}, status=status.HTTP_400_BAD_REQUEST)

        if new_password != re_new_password:
            return Response({'error': 'Las contraseñas no coinciden.'}, status=status.HTTP_400_BAD_REQUEST)

        if not user.check_password(current_password):
            return Response({'error': 'La contraseña actual es incorrecta.'}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.must_change_password = False
        user.save()
        return Response({'message': 'Contraseña actualizada correctamente.'}, status=status.HTTP_200_OK)
