from django.urls import path
from .views import StockLevelsView, LowStockView, RestockView, InventoryLogListView

urlpatterns = [
    path('', StockLevelsView.as_view(), name='inventory-levels'),
    path('low-stock/', LowStockView.as_view(), name='inventory-low-stock'),
    path('restock/', RestockView.as_view(), name='inventory-restock'),
    path('logs/', InventoryLogListView.as_view(), name='inventory-logs'),
]
