from djoser.serializers import UserSerializer as BaseUserSerializer, UserCreateSerializer as BaseUserCreateSerializer
from django.contrib.auth import get_user_model
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework import serializers
from .models import Store

User = get_user_model()

class UserCreateSerializer(BaseUserCreateSerializer):
    class Meta(BaseUserCreateSerializer.Meta):
        model = User
        fields = ('id', 'email', 'password', 'first_name', 'last_name')

    def create(self, validated_data):
        # Los registros públicos desde la Landing Page son Administradores (Owners)
        validated_data['role'] = 'admin'
        return super().create(validated_data)

class StoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Store
        fields = ('id', 'name', 'is_premium', 'max_products', 'max_users')

# para editar propio usuario /users/me/
class CurrentUserSerializer(BaseUserSerializer):
    store = StoreSerializer(read_only=True)

    class Meta(BaseUserSerializer.Meta):
        model = User
        fields = ('id', 'email', 'first_name', 'last_name', 'role', 'is_active', 'is_staff', 'store')
        read_only_fields = ('role', 'is_staff')
        permissionClasses = [IsAuthenticated]

#para asignar administrador o vendedor /users/{id}/
#para asignar administrador o vendedor /users/{id}/
class UserRoleSerializer(BaseUserSerializer):
    class Meta(BaseUserSerializer.Meta):
        model = User
        fields = ('id', 'email', 'first_name', 'last_name', 'role', 'is_active', 'is_staff', 'store')
        permissionClasses = [IsAdminUser]

class EmployeeSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('id', 'email', 'first_name', 'last_name', 'password', 'is_active')

    def create(self, validated_data):
        password = validated_data.pop('password')
        # El store, role e is_active=False se asignarán en el perform_create del ViewSet
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user
