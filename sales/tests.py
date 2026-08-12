from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from rest_framework import status
from products.models import Product, Category
from clients.models import Client
from sales.models import Sale
from decimal import Decimal
from django.core import mail

User = get_user_model()

class SalesTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='test@example.com', password='test')
        self.client.force_authenticate(user=self.user)
        
        self.category = Category.objects.create(name="Electrónica")
        self.product = Product.objects.create(
            name="Laptop",
            sku="LAP-01",
            price=Decimal("1000.00"),
            stock=10,
            category=self.category
        )
        self.product2 = Product.objects.create(
            name="Mouse",
            sku="MOU-01",
            price=Decimal("50.00"),
            stock=2,
            category=self.category
        )
        self.client_obj = Client.objects.create(
            name="Ulises",
            email="cliente@test.com",
            phone="1234567890"
        )

    def test_bulk_sync_happy_path(self):
        """
        Happy Path: Sincronizar un lote de ventas offline exitosamente.
        """
        data = [
            {
                "client": self.client_obj.id,
                "details": [
                    {"product": self.product.id, "quantity": 1}
                ]
            }
        ]
        response = self.client.post('/api/sales/bulk-sync/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['synced'], 1)
        self.assertEqual(len(response.data['errors']), 0)
        
        # Verificar stock
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 9)

    def test_bulk_sync_partial_failure(self):
        """
        Sad Path: Si una venta falla por falta de stock, el lote no se cae, solo esa venta reporta error.
        """
        data = [
            {
                # Venta A (Exitosa)
                "client": self.client_obj.id,
                "details": [{"product": self.product.id, "quantity": 1}]
            },
            {
                # Venta B (Falla por stock, solo tenemos 2 Mouse)
                "client": self.client_obj.id,
                "details": [{"product": self.product2.id, "quantity": 5}]
            }
        ]
        response = self.client.post('/api/sales/bulk-sync/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_207_MULTI_STATUS)
        self.assertEqual(response.data['synced'], 1)
        self.assertEqual(len(response.data['errors']), 1)
        self.assertIn("No hay suficiente stock", str(response.data['errors'][0]['error']))

        # Verificar stock: Laptop bajó, Mouse no bajó
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 9)
        self.product2.refresh_from_db()
        self.assertEqual(self.product2.stock, 2)

    def test_sale_email_ticket(self):
        """
        Happy Path: Al crear una venta normal (no bulk), si el cliente tiene correo, se envía un ticket.
        """
        data = {
            "client": self.client_obj.id,
            "details": [{"product": self.product.id, "quantity": 1}]
        }
        response = self.client.post('/api/sales/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verificar que se generó un correo en la bandeja de salida (test mode)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "Tu Ticket de Compra en StoreHub - Venta #1")
        self.assertEqual(mail.outbox[0].to, ["cliente@test.com"])
