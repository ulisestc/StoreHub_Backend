from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from rest_framework import status
from django.urls import reverse

User = get_user_model()

class AccountsTestCase(APITestCase):
    def setUp(self):
        # La creación de usuario admin debería generar el Store automáticamente
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpassword',
            first_name='Juan',
            role='admin'
        )
        self.user.refresh_from_db()
        self.client.force_authenticate(user=self.user)

    def test_store_profile_created_automatically(self):
        """
        Happy Path: Comprueba que al crear un usuario admin, el Store se crea.
        """
        self.assertIsNotNone(self.user.store)
        self.assertFalse(self.user.store.is_premium)
        self.assertEqual(self.user.store.name, "Tienda de Juan")
        self.assertEqual(self.user.store.max_products, 50)
        self.assertEqual(self.user.store.max_users, 2)

    def test_current_user_endpoint_includes_profile(self):
        """
        Happy Path: El endpoint /api/auth/users/me/ devuelve el objeto anidado store.
        """
        response = self.client.get('/api/auth/users/me/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('store', response.data)
        self.assertFalse(response.data['store']['is_premium'])

    def test_cannot_modify_is_premium_via_me_endpoint(self):
        """
        Sad Path: Un usuario no debería poder escalar sus privilegios modificando is_premium en /api/auth/users/me/
        """
        data = {
            "first_name": "Pedro",
            "store": {
                "is_premium": True
            }
        }
        response = self.client.patch('/api/auth/users/me/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Refrescar desde DB
        self.user.store.refresh_from_db()
        self.assertFalse(self.user.store.is_premium, "El usuario pudo escalar is_premium a True de manera no autorizada.")
