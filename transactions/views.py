import uuid
from django.db import transaction as db_transaction
from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from products.models import Product
from inventory.models import InventoryLog
from .models import Transaction
from .serializers import TransactionSerializer, CheckoutSerializer


class CheckoutView(APIView):
    """
    POST /api/transactions/checkout/
    Accepts: { "items": [ { "product_id": 1, "quantity": 2 }, ... ] }
    Validates stock, creates transactions, deducts inventory, logs changes.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CheckoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        items = serializer.validated_data['items']
        receipt_number = uuid.uuid4().hex[:12].upper()

        # ── Validate all items before modifying anything ──
        product_map = {}
        errors = []
        for item in items:
            try:
                product = Product.objects.get(id=item['product_id'], is_active=True)
            except Product.DoesNotExist:
                errors.append(f"Product with id {item['product_id']} not found.")
                continue

            if product.quantity < item['quantity']:
                errors.append(
                    f"Insufficient stock for '{product.name}'. "
                    f"Available: {product.quantity}, Requested: {item['quantity']}."
                )
                continue

            product_map[item['product_id']] = {
                'product': product,
                'quantity': item['quantity'],
            }

        if errors:
            return Response({'errors': errors}, status=status.HTTP_400_BAD_REQUEST)

        # ── Execute checkout atomically ──
        created_transactions = []
        with db_transaction.atomic():
            for pid, info in product_map.items():
                product = info['product']
                qty = info['quantity']
                total = product.price * qty

                # Create transaction record
                txn = Transaction.objects.create(
                    product=product,
                    quantity=qty,
                    unit_price=product.price,
                    total_price=total,
                    cashier=request.user,
                    receipt_number=receipt_number,
                )
                created_transactions.append(txn)

                # Deduct inventory
                product.quantity -= qty
                product.save()

                # Log inventory change
                InventoryLog.objects.create(
                    product=product,
                    change_type='sale',
                    quantity_changed=-qty,
                    quantity_after=product.quantity,
                    performed_by=request.user,
                    notes=f'Checkout receipt #{receipt_number}',
                )

        # ── Build response ──
        grand_total = sum(t.total_price for t in created_transactions)
        return Response(
            {
                'receipt_number': receipt_number,
                'items': TransactionSerializer(created_transactions, many=True).data,
                'grand_total': str(grand_total),
                'message': 'Checkout completed successfully.',
            },
            status=status.HTTP_201_CREATED,
        )


class TransactionListView(generics.ListAPIView):
    """GET /api/transactions/ — Transaction history with filters."""

    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = Transaction.objects.select_related('product', 'cashier')
        product_id = self.request.query_params.get('product_id')
        receipt = self.request.query_params.get('receipt')
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')

        if product_id:
            qs = qs.filter(product_id=product_id)
        if receipt:
            qs = qs.filter(receipt_number=receipt)
        if date_from:
            qs = qs.filter(timestamp__date__gte=date_from)
        if date_to:
            qs = qs.filter(timestamp__date__lte=date_to)
        return qs


class TransactionDetailView(generics.RetrieveAPIView):
    """GET /api/transactions/<id>/ — Single transaction detail."""

    queryset = Transaction.objects.select_related('product', 'cashier')
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]
