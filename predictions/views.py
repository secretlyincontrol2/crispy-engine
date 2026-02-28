import math
import logging
from datetime import date, timedelta

from django.db.models import Sum
from django.db.models.functions import TruncDate
from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from accounts.permissions import IsAdmin
from products.models import Product
from transactions.models import Transaction
from .models import Prediction
from .serializers import PredictionSerializer, ForecastRequestSerializer, RecommendationSerializer

logger = logging.getLogger(__name__)


class ForecastView(APIView):
    """
    POST /api/predictions/forecast/
    Triggers LSTM demand forecast for a product.
    Admin-only.
    """

    permission_classes = [IsAdmin]

    def post(self, request):
        serializer = ForecastRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        product_id = serializer.validated_data['product_id']
        days_ahead = serializer.validated_data.get('days_ahead', 7)

        try:
            product = Product.objects.get(id=product_id, is_active=True)
        except Product.DoesNotExist:
            return Response(
                {'error': f'Product {product_id} not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        # ── Fetch last 30 days of sales ──
        thirty_days_ago = date.today() - timedelta(days=30)
        daily_sales = (
            Transaction.objects
            .filter(product=product, timestamp__date__gte=thirty_days_ago)
            .annotate(sale_date=TruncDate('timestamp'))
            .values('sale_date')
            .annotate(total_qty=Sum('quantity'))
            .order_by('sale_date')
        )
        daily_sales_list = [
            {'date': row['sale_date'], 'total_qty': row['total_qty']}
            for row in daily_sales
        ]

        # ── Try loading the model and running prediction ──
        try:
            from .ml_utils import predict_demand
            predicted = predict_demand(daily_sales_list, float(product.price))
        except FileNotFoundError:
            return Response(
                {
                    'error': 'LSTM model or scaler file not found. '
                             'Please place inventory_lstm_model.pth and data_scaler.gz '
                             'in the ml_models/ directory.',
                    'hn': 'Set AI_MODEL_PATH and AI_SCALER_PATH in settings or env vars.',
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except Exception as e:
            logger.exception("Prediction failed for product %s", product_id)
            return Response(
                {'error': f'Prediction failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # ── Store predictions for each day ahead ──
        predictions = []
        for i in range(1, days_ahead + 1):
            pred_date = date.today() + timedelta(days=i)
            pred, _ = Prediction.objects.update_or_create(
                product=product,
                prediction_date=pred_date,
                defaults={'predicted_demand': predicted},
            )
            predictions.append(pred)

        return Response(
            {
                'product': product.name,
                'predicted_demand_per_day': predicted,
                'days_ahead': days_ahead,
                'total_predicted': predicted * days_ahead,
                'predictions': PredictionSerializer(predictions, many=True).data,
                'message': 'Forecast generated successfully.',
            },
            status=status.HTTP_200_OK,
        )


class PredictionListView(generics.ListAPIView):
    """GET /api/predictions/ — Stored predictions with optional filters."""

    serializer_class = PredictionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = Prediction.objects.select_related('product')
        product_id = self.request.query_params.get('product_id')
        if product_id:
            qs = qs.filter(product_id=product_id)
        return qs


class RecommendationView(APIView):
    """
    GET /api/predictions/recommendations/
    Restocking recommendations based on latest forecasts.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        products = Product.objects.filter(is_active=True)
        recommendations = []

        for product in products:
            latest_pred = (
                Prediction.objects
                .filter(product=product)
                .order_by('-prediction_date')
                .first()
            )

            demand = latest_pred.predicted_demand if latest_pred else 0
            gap = demand - product.quantity

            if gap > 0:
                urgency = 'critical' if product.quantity <= product.low_stock_threshold else 'warning'
                restock = math.ceil(gap * 1.2)  # 20% safety buffer
            else:
                urgency = 'ok'
                restock = 0

            recommendations.append({
                'product_id': product.id,
                'product_name': product.name,
                'current_stock': product.quantity,
                'predicted_demand': demand,
                'recommended_restock': restock,
                'urgency': urgency,
            })

        # Sort: critical first, then warning, then ok
        order = {'critical': 0, 'warning': 1, 'ok': 2}
        recommendations.sort(key=lambda r: order.get(r['urgency'], 3))

        serializer = RecommendationSerializer(recommendations, many=True)
        return Response(serializer.data)
