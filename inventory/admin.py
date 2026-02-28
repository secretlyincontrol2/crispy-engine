from django.contrib import admin
from .models import InventoryLog


@admin.register(InventoryLog)
class InventoryLogAdmin(admin.ModelAdmin):
    list_display = ('product', 'change_type', 'quantity_changed', 'quantity_after', 'performed_by', 'timestamp')
    list_filter = ('change_type', 'timestamp')
    search_fields = ('product__name',)
