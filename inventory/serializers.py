from rest_framework import serializers
from .models import InventoryLog
from products.serializers import ProductSerializer


class InventoryLogSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    performed_by_username = serializers.CharField(
        source='performed_by.username', read_only=True, default=None
    )

    class Meta:
        model = InventoryLog
        fields = (
            'id', 'product', 'product_name', 'change_type',
            'quantity_changed', 'quantity_after',
            'performed_by', 'performed_by_username',
            'notes', 'timestamp',
        )
        read_only_fields = fields


class RestockSerializer(serializers.Serializer):
    """Serializer for restocking a product."""

    product_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)
    notes = serializers.CharField(required=False, default='')


class StockLevelSerializer(serializers.Serializer):
    """Read-only serializer for current stock levels."""

    id = serializers.IntegerField()
    name = serializers.CharField()
    quantity = serializers.IntegerField()
    low_stock_threshold = serializers.IntegerField()
    is_low_stock = serializers.BooleanField()
    price = serializers.DecimalField(max_digits=10, decimal_places=2)
