from django.urls import path
from .views import CheckoutView, TransactionListView, TransactionDetailView

urlpatterns = [
    path('checkout/', CheckoutView.as_view(), name='transaction-checkout'),
    path('', TransactionListView.as_view(), name='transaction-list'),
    path('<int:pk>/', TransactionDetailView.as_view(), name='transaction-detail'),
]
