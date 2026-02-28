from rest_framework import serializers
from .models import Transaction


class TransactionSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    cashier_name = serializers.CharField(source='cashier.username', read_only=True, default=None)

    class Meta:
        model = Transaction
        fields = (
            'id', 'product', 'product_name', 'quantity',
            'unit_price', 'total_price', 'cashier', 'cashier_name',
            'receipt_number', 'timestamp',
        )
        read_only_fields = fields


class CheckoutItemSerializer(serializers.Serializer):
    """One item in a checkout request."""

    product_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)


class CheckoutSerializer(serializers.Serializer):
    """Accepts a list of items for checkout."""

    items = CheckoutItemSerializer(many=True)
