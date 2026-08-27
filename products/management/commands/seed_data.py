from decimal import Decimal
import random
from datetime import timedelta
from django.utils import timezone
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
        self.stdout.write(self.style.SUCCESS('🌱 Iniciando carga de datos iniciales (Mini Súper)...'))

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
                store = Store.objects.create(name=f"Mini Súper de {admin_user.first_name}")
                admin_user.store = store
                admin_user.save()
            else:
                store.name = "Mini Súper San José"
            
            # Convertir a Premium
            store.is_premium = True
            store.max_products = 5000
            store.save()
                    
            self.stdout.write(self.style.SUCCESS('  [+] Usuario Admin y Tienda Premium: admin@storehub.com / admin12345'))

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
                self.stdout.write(self.style.SUCCESS('  [+] Usuario Vendedor: vendedor@storehub.com / seller12345'))

            # Limpiar datos previos si existen (para evitar duplicados al correr multiples veces)
            Category.objects.filter(store=store).delete()
            Product.objects.filter(store=store).delete()
            Client.objects.filter(store=store).delete()
            Sale.objects.filter(store=store).delete()

            # 2. Crear Categorías
            categories_data = [
                {'name': 'Bebidas y Licores', 'description': 'Refrescos, jugos, cervezas y licores'},
                {'name': 'Botanas y Dulces', 'description': 'Frituras, galletas, chocolates y dulces'},
                {'name': 'Lácteos y Refrigerados', 'description': 'Leche, quesos, yogur y embutidos'},
                {'name': 'Abarrotes Básicos', 'description': 'Arroz, frijol, aceite, enlatados'},
                {'name': 'Cuidado Personal', 'description': 'Jabón, shampoo, papel higiénico'}
            ]

            category_objs = {}
            for cat_info in categories_data:
                cat = Category.objects.create(
                    store=store,
                    name=cat_info['name'],
                    description=cat_info['description']
                )
                category_objs[cat.name] = cat

            self.stdout.write(self.style.SUCCESS(f'  [+] {len(category_objs)} Categorías procesadas.'))

            # 3. Crear Productos
            products_data = [
                {'name': 'Coca Cola Retornable 2.5L', 'sku': 'BEB-001', 'price': '38.00', 'cost_price': '28.00', 'stock': 45, 'cat': 'Bebidas y Licores', 'desc': 'Refresco de cola'},
                {'name': 'Cerveza Victoria Lata 355ml', 'sku': 'BEB-002', 'price': '22.00', 'cost_price': '15.00', 'stock': 120, 'cat': 'Bebidas y Licores', 'desc': 'Cerveza clara'},
                {'name': 'Jugo Jumex Durazno 1L', 'sku': 'BEB-003', 'price': '25.00', 'cost_price': '18.00', 'stock': 30, 'cat': 'Bebidas y Licores', 'desc': 'Jugo de fruta'},
                
                {'name': 'Sabritas Sal 170g', 'sku': 'BOT-001', 'price': '42.00', 'cost_price': '29.00', 'stock': 25, 'cat': 'Botanas y Dulces', 'desc': 'Papas fritas tamaño familiar'},
                {'name': 'Galletas Chokis 76g', 'sku': 'BOT-002', 'price': '18.00', 'cost_price': '12.00', 'stock': 50, 'cat': 'Botanas y Dulces', 'desc': 'Galletas con chispas de chocolate'},
                
                {'name': 'Leche Santa Clara Entera 1L', 'sku': 'LAC-001', 'price': '28.00', 'cost_price': '21.00', 'stock': 40, 'cat': 'Lácteos y Refrigerados', 'desc': 'Leche de vaca'},
                {'name': 'Queso Panela Fud 400g', 'sku': 'LAC-002', 'price': '65.00', 'cost_price': '45.00', 'stock': 15, 'cat': 'Lácteos y Refrigerados', 'desc': 'Queso fresco'},
                {'name': 'Jamón de Pavo Fud 250g', 'sku': 'LAC-003', 'price': '48.00', 'cost_price': '35.00', 'stock': 20, 'cat': 'Lácteos y Refrigerados', 'desc': 'Rebanado'},

                {'name': 'Aceite Nutrioli 946ml', 'sku': 'ABA-001', 'price': '52.00', 'cost_price': '38.00', 'stock': 35, 'cat': 'Abarrotes Básicos', 'desc': 'Aceite vegetal puro de soya'},
                {'name': 'Arroz Verde Valle 1Kg', 'sku': 'ABA-002', 'price': '38.00', 'cost_price': '26.00', 'stock': 50, 'cat': 'Abarrotes Básicos', 'desc': 'Arroz súper extra'},
                {'name': 'Frijol Pinto Verde Valle 900g', 'sku': 'ABA-003', 'price': '45.00', 'cost_price': '31.00', 'stock': 60, 'cat': 'Abarrotes Básicos', 'desc': 'Frijol pinto limpio'},

                {'name': 'Papel Higiénico Pétalo 4 Rollos', 'sku': 'CUI-001', 'price': '35.00', 'cost_price': '22.00', 'stock': 80, 'cat': 'Cuidado Personal', 'desc': 'Papel higiénico hoja doble'},
                {'name': 'Shampoo Head & Shoulders 375ml', 'sku': 'CUI-002', 'price': '85.00', 'cost_price': '55.00', 'stock': 20, 'cat': 'Cuidado Personal', 'desc': 'Shampoo limpieza profunda'}
            ]

            product_objs = []
            for p in products_data:
                prod = Product.objects.create(
                    store=store,
                    sku=p['sku'],
                    name=p['name'],
                    price=Decimal(p['price']),
                    cost_price=Decimal(p['cost_price']),
                    stock=p['stock'],
                    category=category_objs[p['cat']],
                    description=p['desc'],
                    is_active=True
                )
                product_objs.append(prod)

            self.stdout.write(self.style.SUCCESS(f'  [+] {len(product_objs)} Productos creados.'))

            # 4. Crear Clientes
            clients_data = [
                {'name': 'Doña Rosa (Vecina)', 'email': 'rosa.vecina@gmail.com', 'phone': '2221112233'},
                {'name': 'Taller Mecánico El Tuercas', 'email': 'taller@hotmail.com', 'phone': '2224445566'},
                {'name': 'Escuela Primaria Morelos', 'email': 'primaria.morelos@sep.gob.mx', 'phone': '2229998877'}
            ]

            client_objs = []
            for c in clients_data:
                client = Client.objects.create(
                    store=store,
                    name=c['name'],
                    email=c['email'],
                    phone=c['phone']
                )
                client_objs.append(client)

            self.stdout.write(self.style.SUCCESS(f'  [+] {len(client_objs)} Clientes creados.'))

            # 5. Generar 30 días de ventas para alimentar el BI y el Chatbot
            now = timezone.now()
            total_ventas_creadas = 0
            
            for i in range(30):
                # Calcular la fecha hacia atrás
                current_date = now - timedelta(days=29 - i)
                
                # Crear entre 5 y 15 ventas por día
                num_sales_today = random.randint(5, 15)
                
                # Simular picos de venta los fines de semana
                if current_date.weekday() >= 5: # Sábado o Domingo
                    num_sales_today += random.randint(5, 10)
                
                for j in range(num_sales_today):
                    # Hora aleatoria entre las 8:00 AM y las 9:00 PM
                    sale_time = current_date.replace(hour=random.randint(8, 20), minute=random.randint(0, 59))
                    
                    # 40% de las ventas son a clientes frecuentes (Lealtad), 60% público en general
                    client = random.choice(client_objs) if random.random() < 0.4 else None
                    
                    # Entre 1 y 5 productos por venta (UPT - Units Per Transaction)
                    num_items = random.randint(1, 5)
                    selected_products = random.sample(product_objs, num_items)
                    
                    subtotal = Decimal('0.00')
                    sale_details = []
                    
                    for prod in selected_products:
                        qty = random.randint(1, 3)
                        price = prod.price
                        subtotal += (price * qty)
                        sale_details.append({
                            'product': prod,
                            'quantity': qty,
                            'price_at_sale': price
                        })
                        
                    tax = subtotal * Decimal('0.16')
                    total = subtotal + tax
                    
                    sale = Sale.objects.create(
                        store=store,
                        user=random.choice([admin_user, seller_user]),
                        client=client,
                        subtotal=subtotal,
                        impuestos=tax,
                        total=total,
                    )
                    
                    # Hack: Modificar la fecha de creación manualmente ignorando auto_now_add
                    Sale.objects.filter(id=sale.id).update(created_at=sale_time)
                    
                    for detail in sale_details:
                        SaleDetail.objects.create(
                            sale=sale,
                            product=detail['product'],
                            quantity=detail['quantity'],
                            price_at_sale=detail['price_at_sale']
                        )
                        
                    total_ventas_creadas += 1

            self.stdout.write(self.style.SUCCESS(f'  [+] {total_ventas_creadas} Ventas generadas en los últimos 30 días.'))

        self.stdout.write(self.style.SUCCESS('🎉 ¡Carga de datos (Mini Súper) completada exitosamente!'))

