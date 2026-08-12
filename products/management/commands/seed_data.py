from decimal import Decimal
import random
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction

from accounts.models import Store
from products.models import Category, Product
from clients.models import Client
from inventory.models import InventoryMovement
from sales.models import Sale, SaleDetail

User = get_user_model()

class Command(BaseCommand):
    help = 'Pobla la base de datos con datos realistas para pruebas y demostraciones en la Feria de Proyectos FCC BUAP 2036.'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('🌱 Iniciando carga de datos iniciales (seed_data)...'))

        with transaction.atomic():
            # 1. Crear Usuarios de prueba (Admin y Vendedor) y Tienda
            admin_user, created = User.objects.get_or_create(
                email='admin@storehub.com',
                defaults={
                    'first_name': 'Administrador',
                    'last_name': 'StoreHub',
                    'role': 'admin',
                    'is_staff': True,
                    'is_superuser': True
                }
            )
            
            if created:
                admin_user.set_password('admin12345')
                admin_user.save()
                
            admin_user.refresh_from_db()
            store = admin_user.store
            
            if not store:
                store = Store.objects.create(name=f"Tienda de {admin_user.first_name}")
                admin_user.store = store
                admin_user.save()
            
            # Convertir a Premium
            store.is_premium = True
            store.max_products = 5000
            store.save()
                    
            self.stdout.write(self.style.SUCCESS('  [+] Usuario Admin creado y Tienda asignada: admin@storehub.com / admin12345 (PREMIUM)'))

            seller_user, created_seller = User.objects.get_or_create(
                email='vendedor@storehub.com',
                defaults={
                    'first_name': 'Carlos',
                    'last_name': 'Mendoza',
                    'role': 'seller',
                    'is_staff': False,
                    'store': store
                }
            )
            if created_seller:
                seller_user.set_password('seller12345')
                seller_user.save()
                self.stdout.write(self.style.SUCCESS('  [+] Usuario Vendedor creado: vendedor@storehub.com / seller12345'))

            # 2. Crear Categorías
            categories_data = [
                {'name': 'Electrónica y Cómputo', 'description': 'Dispositivos electrónicos, accesorios y periféricos'},
                {'name': 'Papelería y Oficina', 'description': 'Artículos escolares, de oficina y suministros'},
                {'name': 'Abarrotes y Bebidas', 'description': 'Productos alimenticios, refrescos y botanas'},
                {'name': 'Accesorios y Moda', 'description': 'Artículos de vestimenta, mochilas y accesorios'}
            ]

            category_objs = {}
            for cat_info in categories_data:
                cat, _ = Category.objects.get_or_create(
                    store=store,
                    name=cat_info['name'],
                    defaults={'description': cat_info['description']}
                )
                category_objs[cat.name] = cat

            self.stdout.write(self.style.SUCCESS(f'  [+] {len(category_objs)} Categorías procesadas.'))

            # 3. Crear Productos
            products_data = [
                {'name': 'Laptop Lenovo IdeaPad 15"', 'sku': 'ELE-001', 'barcode': '750100000001', 'price': '12999.00', 'cost_price': '9500.00', 'stock': 15, 'cat': 'Electrónica y Cómputo', 'desc': 'Intel Core i5, 16GB RAM, 512GB SSD'},
                {'name': 'Mouse Inalámbrico Logitech M185', 'sku': 'ELE-002', 'barcode': '750100000002', 'price': '299.00', 'cost_price': '180.00', 'stock': 50, 'cat': 'Electrónica y Cómputo', 'desc': 'Conexión 2.4GHz USB nanorreceptor'},
                {'name': 'Teclado Mecánico RGB Redragon', 'sku': 'ELE-003', 'barcode': '750100000003', 'price': '899.00', 'cost_price': '550.00', 'stock': 25, 'cat': 'Electrónica y Cómputo', 'desc': 'Switches Red silenciosos, iluminación RGB'},
                {'name': 'Audífonos Bluetooth Sony WH-CH520', 'sku': 'ELE-004', 'barcode': '750100000004', 'price': '1199.00', 'cost_price': '750.00', 'stock': 20, 'cat': 'Electrónica y Cómputo', 'desc': 'Hasta 50h de batería, micrófono integrado'},
                {'name': 'Monitor LG 24" Full HD 75Hz', 'sku': 'ELE-005', 'barcode': '750100000005', 'price': '2499.00', 'cost_price': '1700.00', 'stock': 8, 'cat': 'Electrónica y Cómputo', 'desc': 'Panel IPS, HDMI y VGA'},

                {'name': 'Cuaderno Profesional Scribe 100h', 'sku': 'PAP-001', 'barcode': '750200000001', 'price': '45.00', 'cost_price': '25.00', 'stock': 120, 'cat': 'Papelería y Oficina', 'desc': 'Pasta dura, cuadro chico'},
                {'name': 'Caja de Plumas Bic Azul 12 pzs', 'sku': 'PAP-002', 'barcode': '750200000002', 'price': '78.00', 'cost_price': '45.00', 'stock': 80, 'cat': 'Papelería y Oficina', 'desc': 'Punto mediano 1.0mm'},
                {'name': 'Paquete Hojas Blancas Carta 500h', 'sku': 'PAP-003', 'barcode': '750200000003', 'price': '115.00', 'cost_price': '75.00', 'stock': 40, 'cat': 'Papelería y Oficina', 'desc': 'Papel bond 75g/m2'},
                {'name': 'Mochila Escolar Impermeable BUAP', 'sku': 'PAP-004', 'barcode': '750200000004', 'price': '450.00', 'cost_price': '250.00', 'stock': 5, 'cat': 'Papelería y Oficina', 'desc': 'Compartimento para laptop 15.6"'},

                {'name': 'Café Soluble Nescafé Clásico 200g', 'sku': 'ABA-001', 'barcode': '750300000001', 'price': '110.00', 'cost_price': '78.00', 'stock': 60, 'cat': 'Abarrotes y Bebidas', 'desc': 'Café 100% puro soluble'},
                {'name': 'Agua Embotellada Ciel 1.5L', 'sku': 'ABA-002', 'barcode': '750300000002', 'price': '18.00', 'cost_price': '9.00', 'stock': 150, 'cat': 'Abarrotes y Bebidas', 'desc': 'Agua purificada sin gas'},
                {'name': 'Galletas Emperador Chocolate 109g', 'sku': 'ABA-003', 'barcode': '750300000003', 'price': '22.00', 'cost_price': '13.00', 'stock': 90, 'cat': 'Abarrotes y Bebidas', 'desc': 'Galletas rellenas sabor chocolate'},

                {'name': 'Termo Acero Inoxidable 800ml', 'sku': 'ACC-001', 'barcode': '750400000001', 'price': '280.00', 'cost_price': '140.00', 'stock': 30, 'cat': 'Accesorios y Moda', 'desc': 'Conserva bebidas frías y calientes 12h'},
                {'name': 'Llavero Conmemorativo FCC BUAP', 'sku': 'ACC-002', 'barcode': '750400000002', 'price': '60.00', 'cost_price': '20.00', 'stock': 200, 'cat': 'Accesorios y Moda', 'desc': 'Edición especial Feria de Proyectos 2036'}
            ]

            product_objs = []
            for p in products_data:
                prod, _ = Product.objects.get_or_create(
                    store=store,
                    sku=p['sku'],
                    defaults={
                        'name': p['name'],
                        'barcode': p['barcode'],
                        'price': Decimal(p['price']),
                        'cost_price': Decimal(p['cost_price']),
                        'stock': p['stock'],
                        'category': category_objs[p['cat']],
                        'description': p['desc'],
                        'is_active': True
                    }
                )
                product_objs.append(prod)

            self.stdout.write(self.style.SUCCESS(f'  [+] {len(product_objs)} Productos creados/verificados.'))

            # 4. Crear Clientes
            clients_data = [
                {'name': 'Juan Pérez Gómez', 'email': 'juan.perez@gmail.com', 'phone': '2221234567'},
                {'name': 'María Fernanda López', 'email': 'mafer.lopez@outlook.com', 'phone': '2227654321'},
                {'name': 'Laboratorio de Cómputo FCC BUAP', 'email': 'lab.computo@buap.mx', 'phone': '2222295500'},
                {'name': 'Roberto Sánchez Ruiz', 'email': 'roberto.sanchez@yahoo.com', 'phone': '2223334455'}
            ]

            client_objs = []
            for c in clients_data:
                client, _ = Client.objects.get_or_create(
                    store=store,
                    email=c['email'],
                    defaults={'name': c['name'], 'phone': c['phone']}
                )
                client_objs.append(client)

            self.stdout.write(self.style.SUCCESS(f'  [+] {len(client_objs)} Clientes creados.'))

            # 5. Crear Movimientos de Inventario Iniciales
            for prod in product_objs[:5]:
                InventoryMovement.objects.get_or_create(
                    product=prod,
                    type='in',
                    quantity=prod.stock,
                    user=admin_user
                )

            # 6. Crear Ventas de Ejemplo
            if Sale.objects.filter(store=store).count() == 0:
                sale1_subtotal = Decimal('299.00') + Decimal('899.00')
                sale1_tax = sale1_subtotal * Decimal('0.16')
                sale1_total = sale1_subtotal + sale1_tax

                sale1 = Sale.objects.create(
                    store=store,
                    user=seller_user,
                    client=client_objs[0],
                    subtotal=sale1_subtotal,
                    impuestos=sale1_tax,
                    total=sale1_total
                )
                SaleDetail.objects.create(sale=sale1, product=product_objs[1], quantity=1, price_at_sale=Decimal('299.00'))
                SaleDetail.objects.create(sale=sale1, product=product_objs[2], quantity=1, price_at_sale=Decimal('899.00'))

                sale2_subtotal = Decimal('12999.00')
                sale2_tax = sale2_subtotal * Decimal('0.16')
                sale2_total = sale2_subtotal + sale2_tax

                sale2 = Sale.objects.create(
                    store=store,
                    user=admin_user,
                    client=client_objs[2],
                    subtotal=sale2_subtotal,
                    impuestos=sale2_tax,
                    total=sale2_total
                )
                SaleDetail.objects.create(sale=sale2, product=product_objs[0], quantity=1, price_at_sale=Decimal('12999.00'))

                self.stdout.write(self.style.SUCCESS('  [+] Ventas de prueba e historial generados con éxito.'))

        self.stdout.write(self.style.SUCCESS('🎉 ¡Carga de datos iniciales (seed_data) completada exitosamente!'))
