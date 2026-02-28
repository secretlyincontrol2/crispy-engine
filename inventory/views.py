from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from accounts.permissions import IsAdmin
from products.models import Product
from .models import InventoryLog
from .serializers import InventoryLogSerializer, RestockSerializer, StockLevelSerializer


class StockLevelsView(APIView):
    """GET /api/inventory/ — Current stock levels for all active products."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        products = Product.objects.filter(is_active=True).values(
            'id', 'name', 'quantity', 'low_stock_threshold', 'price'
        )
        data = []
        for p in products:
            p['is_low_stock'] = p['quantity'] <= p['low_stock_threshold']
            data.append(p)
        serializer = StockLevelSerializer(data, many=True)
        return Response(serializer.data)


class LowStockView(APIView):
    """GET /api/inventory/low-stock/ — Products below their threshold."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        products = Product.objects.filter(is_active=True)
        low = [
            {
                'id': p.id,
                'name': p.name,
                'quantity': p.quantity,
                'low_stock_threshold': p.low_stock_threshold,
                'is_low_stock': True,
                'price': p.price,
            }
            for p in products if p.is_low_stock
        ]
        serializer = StockLevelSerializer(low, many=True)
        return Response(serializer.data)


class RestockView(APIView):
    """POST /api/inventory/restock/ — Restock a product (admin-only)."""

    permission_classes = [IsAdmin]

    def post(self, request):
        serializer = RestockSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        product = get_object_or_404(Product, id=serializer.validated_data['product_id'])
        qty = serializer.validated_data['quantity']

        product.quantity += qty
        product.save()

        log = InventoryLog.objects.create(
            product=product,
            change_type='restock',
            quantity_changed=qty,
            quantity_after=product.quantity,
            performed_by=request.user,
            notes=serializer.validated_data.get('notes', ''),
        )

        return Response(
            {
                'message': f'Restocked {product.name} by {qty} units.',
                'new_quantity': product.quantity,
                'log': InventoryLogSerializer(log).data,
            },
            status=status.HTTP_200_OK,
        )


class InventoryLogListView(generics.ListAPIView):
    """GET /api/inventory/logs/ — Audit log of inventory changes."""

    serializer_class = InventoryLogSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = InventoryLog.objects.select_related('product', 'performed_by')
        product_id = self.request.query_params.get('product_id')
        change_type = self.request.query_params.get('change_type')
        if product_id:
            qs = qs.filter(product_id=product_id)
        if change_type:
            qs = qs.filter(change_type=change_type)
        return qs
