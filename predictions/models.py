from django.db import models


class Prediction(models.Model):
    """Stores LSTM demand forecast results."""

    product = models.ForeignKey(
        'products.Product', on_delete=models.CASCADE, related_name='predictions'
    )
    predicted_demand = models.FloatField(help_text='Predicted demand (units).')
    prediction_date = models.DateField(help_text='Date the forecast is for.')
    confidence = models.FloatField(
        null=True, blank=True,
        help_text='Optional confidence score (0–1).',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'predictions'
        ordering = ['-created_at']
        unique_together = ('product', 'prediction_date')

    def __str__(self):
        return f"{self.product.name} — {self.predicted_demand:.0f} units on {self.prediction_date}"
