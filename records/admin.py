from django.contrib import admin
from .models import EggProductionRecord, EggSale

@admin.register(EggProductionRecord)
class EggProductionRecordAdmin(admin.ModelAdmin):
    list_display = ('date', 'eggs_produced', 'eggs_sold', 'eggs_remaining')
    ordering = ('-date',)
    readonly_fields = ('eggs_sold', 'eggs_remaining')  # Prevent manual editing of auto-calculated fields

@admin.register(EggSale)
class EggSaleAdmin(admin.ModelAdmin):
    list_display = ('date', 'buyer_name', 'eggs_sold', 'amount_paid')
    ordering = ('-date',)
