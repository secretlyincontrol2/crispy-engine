from django.contrib import admin
from .models import Prediction


@admin.register(Prediction)
class PredictionAdmin(admin.ModelAdmin):
    list_display = ('product', 'predicted_demand', 'prediction_date', 'created_at')
    list_filter = ('prediction_date',)
    search_fields = ('product__name',)
