from django.urls import path
from .views import ForecastView, PredictionListView, RecommendationView

urlpatterns = [
    path('forecast/', ForecastView.as_view(), name='prediction-forecast'),
    path('', PredictionListView.as_view(), name='prediction-list'),
    path('recommendations/', RecommendationView.as_view(), name='prediction-recommendations'),
]
