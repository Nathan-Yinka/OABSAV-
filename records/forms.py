from django import forms
from .models import EggProductionRecord, EggSale
from django.utils.timezone import now
from django.db import models

class EggProductionRecordForm(forms.ModelForm):
    """Form for adding/editing daily egg production records, including manual stock entry."""
    
    class Meta:
        model = EggProductionRecord
        fields = ['eggs_produced','remark']  # Added manual stock entry
        widgets = {
            'remark': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Enter your remark for today...'}),
        }
        

    def clean(self):
        """Ensure eggs produced and manual stock entry are valid."""
        cleaned_data = super().clean()
        eggs_produced = cleaned_data.get('eggs_produced')
        manual_stock_entry = cleaned_data.get('manual_stock_entry')

        if eggs_produced is None or eggs_produced < 0:
            raise forms.ValidationError("Eggs produced must be a positive number.")

        return cleaned_data


class EggSaleForm(forms.ModelForm):
    """Form for adding and updating egg sales with validation to prevent over-selling."""

    class Meta:
        model = EggSale
        fields = ['buyer_name', 'eggs_sold', 'amount_paid']

    def clean(self):
        """Ensure eggs sold does not exceed available eggs."""
        cleaned_data = super().clean()
        eggs_sold = cleaned_data.get('eggs_sold')

        if eggs_sold is None or eggs_sold < 1:
            raise forms.ValidationError("Please enter a valid number of eggs sold.")

        today = now().date()
        production_record = EggProductionRecord.objects.filter(date=today).first()

        if not production_record:
            raise forms.ValidationError("No production record exists for today. Please add today's production first.")

        # ✅ Get latest `previous_remaining` from **manual stock entry**, otherwise fallback to `eggs_remaining`
        previous_record = EggProductionRecord.objects.filter(date__lt=today).order_by('-date').first()
        previous_remaining = (
            previous_record.manual_stock_entry
            if previous_record and previous_record.manual_stock_entry is not None
            else previous_record.eggs_remaining if previous_record else 0
        )

        # ✅ Calculate `total_available`
        total_available = production_record.eggs_produced + previous_remaining

        # ✅ Get total eggs already sold today (excluding the current sale being updated)
        total_sold_today = EggSale.objects.filter(date=today).aggregate(total=models.Sum('eggs_sold'))['total'] or 0

        # If updating an existing sale, subtract its old value from `total_sold_today`
        if self.instance.pk:
            old_sale = EggSale.objects.get(pk=self.instance.pk)
            total_sold_today -= old_sale.eggs_sold

        # ✅ Ensure eggs sold does not exceed remaining eggs
        available_eggs = total_available - total_sold_today
        print(f"New Sale: {eggs_sold}, Available: {available_eggs}, Previous Sale: {self.instance.eggs_sold if self.instance.pk else 0}")

        if eggs_sold > available_eggs:
            available_crates = available_eggs // 30  # Get full crates
            available_pieces = available_eggs % 30  # Get remaining pieces
            raise forms.ValidationError(
                f"Not enough eggs available for sale. Only {available_crates} crates, {available_pieces} pieces remaining."
            )

        return cleaned_data