from django.db import models
from django.conf import settings


class Transaction(models.Model):
    """A single line-item in a checkout."""

    product = models.ForeignKey(
        'products.Product', on_delete=models.PROTECT, related_name='transactions'
    )
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=12, decimal_places=2)
    cashier = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name='transactions',
    )
    receipt_number = models.CharField(max_length=30, db_index=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'transactions'
        ordering = ['-timestamp']

    def __str__(self):
        return f"#{self.receipt_number} | {self.product.name} x{self.quantity}"
