"""
Root URL configuration.
All API endpoints are namespaced under /api/.
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('accounts.urls')),
    path('api/products/', include('products.urls')),
    path('api/inventory/', include('inventory.urls')),
    path('api/transactions/', include('transactions.urls')),
    path('api/predictions/', include('predictions.urls')),
    path('api/dashboard/', include('dashboard.urls')),
]
