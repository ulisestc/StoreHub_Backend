from djoser.serializers import UserSerializer as BaseUserSerializer, UserCreateSerializer as BaseUserCreateSerializer
from django.contrib.auth import get_user_model
from rest_framework.permissions import IsAuthenticated, IsAdminUser

User=get_user_model()

class UserCreateSerializer(BaseUserCreateSerializer):
    class Meta(BaseUserCreateSerializer.Meta):
        model = User
        fields = ('id', 'email', 'password', 'first_name', 'last_name')
        

from rest_framework import serializers
from .models import StoreProfile

class StoreProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = StoreProfile
        fields = ('store_name', 'is_premium', 'max_products', 'max_users')

# para editar propio usuario /users/me/
class CurrentUserSerializer(BaseUserSerializer):
    profile = StoreProfileSerializer(read_only=True)

    class Meta(BaseUserSerializer.Meta):
        model = User
        fields = ('id', 'email', 'first_name', 'last_name', 'role', 'is_active', 'is_staff', 'profile')
        read_only_fields = ('role', 'is_staff')
        permissionClasses = [IsAuthenticated]

#para asignar administrador o vendedor /users/{id}/
class UserRoleSerializer(BaseUserSerializer):
    class Meta(BaseUserSerializer.Meta):
        model = User
        fields = ('id', 'email', 'first_name', 'last_name', 'role', 'is_active', 'is_staff')
        permissionClasses = [IsAdminUser]
        #read_only_fields = ('id')
