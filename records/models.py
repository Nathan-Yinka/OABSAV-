from django.db import models
from django.utils.timezone import now
from django.core.exceptions import ValidationError

class EggProductionRecord(models.Model):
    date = models.DateField(unique=True, default=now)
    eggs_produced = models.PositiveIntegerField()
    eggs_sold = models.PositiveIntegerField(default=0)
    eggs_remaining = models.PositiveIntegerField(editable=False, default=0)
    manual_stock_entry = models.PositiveIntegerField(null=True, blank=True)  # Stored as total pieces
    remark = models.TextField(blank=True, null=True)

    def save(self, *args, **kwargs):
        """Ensure eggs_remaining correctly accounts for the previous day's remaining eggs."""
        previous_record = EggProductionRecord.objects.filter(date__lt=self.date).order_by('-date').first()
        previous_remaining = (
            previous_record.manual_stock_entry if previous_record and previous_record.manual_stock_entry is not None
            else previous_record.eggs_remaining if previous_record else 0
        )

        # ✅ Correctly calculate eggs_remaining as (Produced + Carry-over - Sold)
        self.eggs_remaining = (self.eggs_produced + previous_remaining) - self.eggs_sold

        super().save(*args, **kwargs)

    @property
    def manual_stock_crates(self):
        """Return manually entered stock in crates."""
        return (self.manual_stock_entry or 0) // 30  # Convert pieces to crates

    @property
    def manual_stock_pieces(self):
        """Return manually entered stock in pieces."""
        return (self.manual_stock_entry or 0) % 30  # Get remaining pieces

    @property
    def audit_discrepancy(self):
        """Calculate audit discrepancy based on manual stock entry."""
        if self.manual_stock_entry is not None:
            print(f"Manual Stock Entry: {self.manual_stock_entry}, Expected Remaining: {self.eggs_remaining}")
            return self.manual_stock_entry - self.eggs_remaining
        return None  # No discrepancy if manual entry is missing

    def clean(self):
        """Ensure eggs sold does not exceed the total available eggs (produced + previous remaining or manual stock)."""
        previous_record = EggProductionRecord.objects.filter(date__lt=self.date).order_by('-date').first()
        
        # ✅ Use manual stock if available, otherwise fallback to eggs_remaining
        previous_remaining = (
            previous_record.manual_stock_entry if previous_record and previous_record.manual_stock_entry is not None
            else previous_record.eggs_remaining if previous_record else 0
        )

        total_available = self.eggs_produced + previous_remaining

        if self.eggs_sold > total_available:
            available_crates = total_available // 30  # Convert pieces to crates
            available_pieces = total_available % 30  # Get remaining pieces

            raise ValidationError(
                f"Eggs sold cannot exceed available stock. Only {available_crates} crates, {available_pieces} pieces available."
            )

    def __str__(self):
        return f"{self.date}: Produced {self.eggs_produced}, Sold {self.eggs_sold}, Remaining {self.eggs_remaining}"

    class Meta:
        ordering = ['date']


class EggSale(models.Model):
    """Model to store daily egg sales per buyer"""
    date = models.DateField(default=now)  # Auto-set to today
    buyer_name = models.CharField(max_length=255)
    eggs_sold = models.PositiveIntegerField()
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)

    def save(self, *args, **kwargs):
        """Ensure each sale updates the corresponding EggProductionRecord."""
        super().save(*args, **kwargs)
        production_record, created = EggProductionRecord.objects.get_or_create(date=self.date)
        production_record.save()  # Trigger recalculation

    def __str__(self):
        return f"{self.date} - {self.buyer_name}: {self.eggs_sold} eggs"

    class Meta:
        ordering = ['date']
