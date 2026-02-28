"""
Management command to seed the database with sample data for testing.
Usage: python manage.py seed_data
"""
import random
from datetime import date, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from products.models import Product
from transactions.models import Transaction
from inventory.models import InventoryLog

User = get_user_model()

SAMPLE_PRODUCTS = [
    {'name': 'Coca-Cola 500ml', 'price': 350.00, 'quantity': 120, 'sku': 'BEV-001', 'description': 'Carbonated soft drink'},
    {'name': 'Indomie Noodles', 'price': 250.00, 'quantity': 200, 'sku': 'FOD-001', 'description': 'Instant noodles pack'},
    {'name': 'Peak Milk 400g', 'price': 1800.00, 'quantity': 80, 'sku': 'DAI-001', 'description': 'Powdered milk tin'},
    {'name': 'Golden Penny Spaghetti', 'price': 650.00, 'quantity': 150, 'sku': 'FOD-002', 'description': '500g spaghetti pack'},
    {'name': 'Dettol Soap', 'price': 450.00, 'quantity': 90, 'sku': 'HYG-001', 'description': 'Antibacterial soap bar'},
    {'name': 'Bournvita 400g', 'price': 2200.00, 'quantity': 60, 'sku': 'BEV-002', 'description': 'Chocolate malt drink'},
    {'name': 'Dangote Sugar 1kg', 'price': 1200.00, 'quantity': 100, 'sku': 'FOD-003', 'description': 'Granulated sugar'},
    {'name': 'Titus Sardine', 'price': 1100.00, 'quantity': 75, 'sku': 'FOD-004', 'description': 'Canned sardine'},
    {'name': 'Close-Up Toothpaste', 'price': 550.00, 'quantity': 110, 'sku': 'HYG-002', 'description': 'Menthol toothpaste'},
    {'name': 'Eva Water 75cl', 'price': 200.00, 'quantity': 300, 'sku': 'BEV-003', 'description': 'Table water bottle'},
    {'name': 'Power Oil 1L', 'price': 1800.00, 'quantity': 45, 'sku': 'FOD-005', 'description': 'Vegetable cooking oil'},
    {'name': 'Milo 500g', 'price': 2800.00, 'quantity': 55, 'sku': 'BEV-004', 'description': 'Energy food drink'},
    {'name': 'Maggi Cube', 'price': 50.00, 'quantity': 500, 'sku': 'FOD-006', 'description': 'Seasoning cube'},
    {'name': 'Omo Detergent 500g', 'price': 650.00, 'quantity': 85, 'sku': 'HYG-003', 'description': 'Washing detergent'},
    {'name': 'Kings Oil 3L', 'price': 5500.00, 'quantity': 30, 'sku': 'FOD-007', 'description': 'Vegetable oil 3 litres'},
]


class Command(BaseCommand):
    help = 'Seed the database with sample users, products, and transactions.'

    def handle(self, *args, **options):
        self.stdout.write('Seeding database...\n')

        # ── Create users ──
        admin, created = User.objects.get_or_create(
            username='admin',
            defaults={'role': 'admin', 'email': 'admin@store.com'},
        )
        if created:
            admin.set_password('admin123')
            admin.save()
            self.stdout.write(self.style.SUCCESS('  ✓ Admin user created (admin / admin123)'))
        else:
            self.stdout.write('  • Admin user already exists')

        cashier, created = User.objects.get_or_create(
            username='cashier',
            defaults={'role': 'cashier', 'email': 'cashier@store.com'},
        )
        if created:
            cashier.set_password('cashier123')
            cashier.save()
            self.stdout.write(self.style.SUCCESS('  ✓ Cashier user created (cashier / cashier123)'))
        else:
            self.stdout.write('  • Cashier user already exists')

        # ── Create products ──
        products = []
        for p_data in SAMPLE_PRODUCTS:
            product, created = Product.objects.get_or_create(
                sku=p_data['sku'],
                defaults=p_data,
            )
            products.append(product)
            if created:
                self.stdout.write(f'  ✓ Product: {product.name}')

        self.stdout.write(self.style.SUCCESS(f'  → {len(products)} products ready'))

        # ── Generate 60 days of sample transactions ──
        self.stdout.write('  Generating 60 days of sample transactions...')
        today = date.today()
        receipt_counter = 0

        for day_offset in range(60, 0, -1):
            sale_date = today - timedelta(days=day_offset)
            # 3–8 transactions per day
            num_transactions = random.randint(3, 8)

            for _ in range(num_transactions):
                product = random.choice(products)
                qty = random.randint(1, 5)
                receipt_counter += 1
                receipt = f'SEED-{receipt_counter:05d}'

                Transaction.objects.create(
                    product=product,
                    quantity=qty,
                    unit_price=product.price,
                    total_price=product.price * qty,
                    cashier=cashier,
                    receipt_number=receipt,
                    # We'll set the timestamp via raw update below
                )

                # Update timestamp to the past date
                from django.utils import timezone
                import datetime
                txn = Transaction.objects.filter(receipt_number=receipt).first()
                if txn:
                    rand_hour = random.randint(8, 20)
                    rand_min = random.randint(0, 59)
                    Transaction.objects.filter(id=txn.id).update(
                        timestamp=timezone.make_aware(
                            datetime.datetime.combine(
                                sale_date,
                                datetime.time(rand_hour, rand_min),
                            )
                        )
                    )

        total_txns = Transaction.objects.count()
        self.stdout.write(self.style.SUCCESS(f'  → {total_txns} transactions created'))

        # ── Summary ──
        self.stdout.write(self.style.SUCCESS('\n✅ Database seeded successfully!'))
        self.stdout.write(f'   Admin login:   admin / admin123')
        self.stdout.write(f'   Cashier login:  cashier / cashier123')
        self.stdout.write(f'   Products:       {len(products)}')
        self.stdout.write(f'   Transactions:   {total_txns}')
