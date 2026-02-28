from rest_framework import serializers
from .models import Product


class ProductSerializer(serializers.ModelSerializer):
    """Full CRUD serializer for Product."""

    is_low_stock = serializers.ReadOnlyField()

    class Meta:
        model = Product
        fields = (
            'id', 'name', 'description', 'price', 'quantity',
            'sku', 'low_stock_threshold', 'is_active',
            'is_low_stock', 'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'created_at', 'updated_at', 'is_low_stock')
