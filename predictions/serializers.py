from rest_framework import serializers
from .models import Prediction


class PredictionSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)

    class Meta:
        model = Prediction
        fields = (
            'id', 'product', 'product_name',
            'predicted_demand', 'prediction_date',
            'confidence', 'created_at',
        )
        read_only_fields = fields


class ForecastRequestSerializer(serializers.Serializer):
    """Request body for triggering a forecast."""

    product_id = serializers.IntegerField()
    days_ahead = serializers.IntegerField(min_value=1, max_value=30, default=7)


class RecommendationSerializer(serializers.Serializer):
    """Restocking recommendation based on forecast."""

    product_id = serializers.IntegerField()
    product_name = serializers.CharField()
    current_stock = serializers.IntegerField()
    predicted_demand = serializers.FloatField()
    recommended_restock = serializers.IntegerField()
    urgency = serializers.CharField()  # 'critical', 'warning', 'ok'
