from django.contrib import admin
from .models import Transaction


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('receipt_number', 'product', 'quantity', 'total_price', 'cashier', 'timestamp')
    list_filter = ('timestamp',)
    search_fields = ('receipt_number', 'product__name')
