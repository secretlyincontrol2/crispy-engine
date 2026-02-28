from django.urls import path
from .views import (
    DashboardSummaryView, SalesTrendsView,
    TopProductsView, ForecastOverviewView,
)

urlpatterns = [
    path('summary/', DashboardSummaryView.as_view(), name='dashboard-summary'),
    path('sales-trends/', SalesTrendsView.as_view(), name='dashboard-sales-trends'),
    path('top-products/', TopProductsView.as_view(), name='dashboard-top-products'),
    path('forecast-overview/', ForecastOverviewView.as_view(), name='dashboard-forecast-overview'),
]
