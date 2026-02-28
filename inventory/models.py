from django.db import models
from django.conf import settings


class InventoryLog(models.Model):
    """Audit log for every inventory change."""

    CHANGE_TYPES = (
        ('sale', 'Sale'),
        ('restock', 'Restock'),
        ('adjustment', 'Adjustment'),
    )

    product = models.ForeignKey(
        'products.Product', on_delete=models.CASCADE, related_name='inventory_logs'
    )
    change_type = models.CharField(max_length=15, choices=CHANGE_TYPES)
    quantity_changed = models.IntegerField(
        help_text='Positive for additions, negative for deductions.'
    )
    quantity_after = models.PositiveIntegerField(
        help_text='Product quantity after this change.'
    )
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='inventory_actions',
    )
    notes = models.TextField(blank=True, default='')
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'inventory_logs'
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.get_change_type_display()} | {self.product.name} | {self.quantity_changed:+d}"
