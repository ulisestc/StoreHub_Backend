from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from rest_framework import status
from django.urls import reverse

User = get_user_model()

class AccountsTestCase(APITestCase):
    def setUp(self):
        # La creación de usuario debería generar el perfil automáticamente
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpassword',
            first_name='Juan'
        )
        self.client.force_authenticate(user=self.user)

    def test_store_profile_created_automatically(self):
        """
        Happy Path: Comprueba que al crear un usuario, el perfil se crea (Feature Flag: is_premium=False).
        """
        self.assertTrue(hasattr(self.user, 'profile'))
        self.assertFalse(self.user.profile.is_premium)
        self.assertEqual(self.user.profile.store_name, "Tienda de Juan")
        self.assertEqual(self.user.profile.max_products, 50)
        self.assertEqual(self.user.profile.max_users, 2)

    def test_current_user_endpoint_includes_profile(self):
        """
        Happy Path: El endpoint /api/users/me/ devuelve el objeto anidado profile.
        """
        response = self.client.get('/api/auth/users/me/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('profile', response.data)
        self.assertFalse(response.data['profile']['is_premium'])

    def test_cannot_modify_is_premium_via_me_endpoint(self):
        """
        Sad Path: Un usuario no debería poder escalar sus privilegios modificando is_premium en /api/users/me/
        """
        data = {
            "first_name": "Pedro",
            "profile": {
                "is_premium": True
            }
        }
        response = self.client.patch('/api/auth/users/me/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Refrescar desde DB
        self.user.refresh_from_db()
        self.assertFalse(self.user.profile.is_premium, "El usuario pudo escalar is_premium a True de manera no autorizada.")
