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
from django.core.mail import send_mail

from .serializers import EmployeeSerializer, StoreSerializer

User = get_user_model()

class StoreConfigView(RetrieveUpdateAPIView):
    serializer_class = StoreSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        if self.request.user.role != 'admin':
            raise PermissionDenied("Solo los administradores pueden editar la configuración de la tienda.")
        return self.request.user.store

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
        
        # Enviar correo con credenciales
        subject = 'Bienvenido a StoreHub'
        login_url = f"http://{settings.DOMAIN}"
        message = f'Hola {user.first_name},\n\nFuiste invitado a {store.name}.\n\nPuedes acceder al sistema desde aquí:\n{login_url}\n\nTu contraseña temporal es: {temp_password}\n\nPor seguridad, el sistema te pedirá cambiarla al iniciar sesión por primera vez.'
        sender_email = settings.EMAIL_HOST_USER if settings.EMAIL_HOST_USER else 'no-reply@storehub.com'
        from_email = f'"{store.name} via StoreHub" <{sender_email}>'
        send_mail(subject, message, from_email, [user.email])

    def perform_destroy(self, instance):
        if self.request.user.role != 'admin':
            raise PermissionDenied("Solo los administradores pueden desactivar empleados.")
        
        # Borramos el usuario de la base de datos para liberar cupo
        instance.delete()

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
