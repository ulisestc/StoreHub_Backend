from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from rest_framework import status
from products.models import Product, Category
from decimal import Decimal

User = get_user_model()

class ProductsTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='test@example.com', password='test', role='admin')
        self.user.refresh_from_db()
        self.client.force_authenticate(user=self.user)
        
        self.category = Category.objects.create(name="Abarrotes", store=self.user.store)
        self.product = Product.objects.create(
            store=self.user.store,
            name="Gansito",
            sku="ABA-010",
            barcode="750100100",
            price=Decimal("15.00"),
            stock=10,
            category=self.category
        )

    def test_search_by_barcode(self):
        """
        Happy Path: El frontend puede buscar un producto por su código de barras.
        """
        response = self.client.get('/api/products/?barcode=750100100')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['name'], "Gansito")

    def test_search_by_partial_barcode(self):
        """
        Happy Path: El search general también debe coincidir con barcode parcial.
        """
        response = self.client.get('/api/products/?search=750100')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_unique_barcode_constraint(self):
        """
        Sad Path: No se puede crear un producto con un código de barras ya existente.
        """
        data = {
            "name": "Chocorrol",
            "sku": "ABA-011",
            "barcode": "750100100",  # Ya existe
            "price": "18.00",
            "stock": 5
        }
        response = self.client.post('/api/products/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('non_field_errors', response.data) # unique_together throws non_field_errors
