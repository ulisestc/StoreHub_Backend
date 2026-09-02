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

class EmployeeTestCase(APITestCase):
    def setUp(self):
        self.admin_user = User.objects.create_user(
            email='admin@example.com',
            password='testpassword',
            first_name='Admin',
            role='admin'
        )
        self.admin_user.refresh_from_db()
        self.client.force_authenticate(user=self.admin_user)
        
    def test_admin_can_create_employee(self):
        """
        Happy Path: Admin puede crear un empleado (cajero) que queda inactivo y pertenece a su tienda.
        """
        data = {
            "email": "cajero@example.com",
            "first_name": "Juan",
            "last_name": "Perez",
            "password": "Password123"
        }
        response = self.client.post('/api/employees/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verificar que se creó y es inactivo
        employee = User.objects.get(email="cajero@example.com")
        self.assertEqual(employee.role, 'seller')
        self.assertEqual(employee.store, self.admin_user.store)
        self.assertFalse(employee.is_active)
        
    def test_employee_creation_quota_limit(self):
        """
        Sad Path: Admin en plan gratis no puede crear más usuarios de su límite (max_users=2, admin ya cuenta como 1).
        Por defecto, max_users = 2, así que admin + 1 cajero = 2 (lleno). El 3er usuario debe fallar.
        """
        User.objects.create_user(
            email='cajero1@example.com',
            password='test',
            store=self.admin_user.store,
            role='seller'
        )
        # Aquí ya hay 2 usuarios en la tienda (Admin + Cajero1)
        data = {
            "email": "cajero2@example.com",
            "first_name": "Pedro",
            "last_name": "Gomez",
            "password": "Password123"
        }
        response = self.client.post('/api/employees/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("límite", str(response.data))
        
    def test_seller_cannot_access_employees_endpoint(self):
        """
        Sad Path: Un cajero no puede ver la lista de empleados.
        """
        seller = User.objects.create_user(
            email='cajero_test@example.com',
            password='test',
            role='seller',
            store=self.admin_user.store
        )
        self.client.force_authenticate(user=seller)
        
        response = self.client.get('/api/employees/')
        self.assertEqual(response.status_code, status.HTTP_200_OK) # Wait, get_queryset returns none
        self.assertEqual(response.data['count'], 0)
        
        response_post = self.client.post('/api/employees/', {
            "email": "x@x.com", 
            "password": "123",
            "first_name": "x",
            "last_name": "x"
        })
        self.assertEqual(response_post.status_code, status.HTTP_403_FORBIDDEN)
