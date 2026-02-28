from datetime import timedelta, date

from django.db.models import Sum, Count
from django.db.models.functions import TruncDate, TruncWeek, TruncMonth
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from products.models import Product
from transactions.models import Transaction
from predictions.models import Prediction


class DashboardSummaryView(APIView):
    """
    GET /api/dashboard/summary/
    Returns high-level KPIs.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        total_products = Product.objects.filter(is_active=True).count()
        low_stock = sum(1 for p in Product.objects.filter(is_active=True) if p.is_low_stock)
        total_transactions = Transaction.objects.count()
        total_revenue = Transaction.objects.aggregate(
            total=Sum('total_price')
        )['total'] or 0

        # Today's stats
        today = date.today()
        today_transactions = Transaction.objects.filter(timestamp__date=today).count()
        today_revenue = Transaction.objects.filter(
            timestamp__date=today
        ).aggregate(total=Sum('total_price'))['total'] or 0

        return Response({
            'total_products': total_products,
            'low_stock_count': low_stock,
            'total_transactions': total_transactions,
            'total_revenue': str(total_revenue),
            'today_transactions': today_transactions,
            'today_revenue': str(today_revenue),
        })


class SalesTrendsView(APIView):
    """
    GET /api/dashboard/sales-trends/?period=daily|weekly|monthly
    Returns aggregated sales data.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        period = request.query_params.get('period', 'daily')
        days = int(request.query_params.get('days', 30))
        start_date = date.today() - timedelta(days=days)

        qs = Transaction.objects.filter(timestamp__date__gte=start_date)

        trunc_fn = {
            'daily': TruncDate,
            'weekly': TruncWeek,
            'monthly': TruncMonth,
        }.get(period, TruncDate)

        trends = (
            qs.annotate(period=trunc_fn('timestamp'))
            .values('period')
            .annotate(
                total_revenue=Sum('total_price'),
                total_quantity=Sum('quantity'),
                transaction_count=Count('id'),
            )
            .order_by('period')
        )

        data = [
            {
                'period': str(t['period']),
                'total_revenue': str(t['total_revenue']),
                'total_quantity': t['total_quantity'],
                'transaction_count': t['transaction_count'],
            }
            for t in trends
        ]
        return Response(data)


class TopProductsView(APIView):
    """
    GET /api/dashboard/top-products/?limit=10
    Top-selling products by total quantity sold.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        limit = int(request.query_params.get('limit', 10))

        top = (
            Transaction.objects
            .values('product__id', 'product__name')
            .annotate(
                total_sold=Sum('quantity'),
                total_revenue=Sum('total_price'),
            )
            .order_by('-total_sold')[:limit]
        )

        data = [
            {
                'product_id': t['product__id'],
                'product_name': t['product__name'],
                'total_sold': t['total_sold'],
                'total_revenue': str(t['total_revenue']),
            }
            for t in top
        ]
        return Response(data)


class ForecastOverviewView(APIView):
    """
    GET /api/dashboard/forecast-overview/
    Latest prediction for each product.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        products = Product.objects.filter(is_active=True)
        data = []

        for product in products:
            latest = (
                Prediction.objects
                .filter(product=product)
                .order_by('-prediction_date')
                .first()
            )
            data.append({
                'product_id': product.id,
                'product_name': product.name,
                'current_stock': product.quantity,
                'predicted_demand': latest.predicted_demand if latest else None,
                'prediction_date': str(latest.prediction_date) if latest else None,
            })

        return Response(data)
