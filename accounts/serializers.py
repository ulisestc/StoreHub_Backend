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
class UserRoleSerializer(BaseUserSerializer):
    class Meta(BaseUserSerializer.Meta):
        model = User
        fields = ('id', 'email', 'first_name', 'last_name', 'role', 'is_active', 'is_staff', 'store')
        permissionClasses = [IsAdminUser]
