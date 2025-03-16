import random
from datetime import timedelta
from django.utils.timezone import now
from records.models import EggProductionRecord, EggSale

# ✅ Start from 3 months ago
start_date = now().date() - timedelta(days=90)

# ✅ Generate records for the last 3 months
for i in range(90):
    date = start_date + timedelta(days=i)
    
    # ✅ Avoid duplicate records
    if EggProductionRecord.objects.filter(date=date).exists():
        continue

    # ✅ Simulate production (200 - 600 eggs daily)
    eggs_produced = random.randint(200, 600)

    # ✅ Fetch previous day's remaining eggs
    previous_record = EggProductionRecord.objects.filter(date__lt=date).order_by('-date').first()
    previous_remaining = (
        previous_record.manual_stock_entry if previous_record and previous_record.manual_stock_entry is not None
        else previous_record.eggs_remaining if previous_record else 0
    )

    # ✅ Simulate manual stock entry (some days have adjustments)
    manual_stock_entry = previous_remaining + eggs_produced - random.randint(50, 250) if random.random() < 0.5 else None

    # ✅ Create production record
    record = EggProductionRecord.objects.create(
        date=date,
        eggs_produced=eggs_produced,
        eggs_sold=0,  # Will be updated later
        eggs_remaining=0,  # Will be updated after sales
        manual_stock_entry=manual_stock_entry,
        remark=random.choice([
            "Normal day", "Adjusted stock", "High sales", "Shortage reported", "Stock correction"
        ]) if random.random() < 0.3 else None
    )

    # ✅ Generate 1-3 sales per day
    total_sold = 0
    for _ in range(random.randint(1, 3)):
        buyer_name = random.choice(["John", "Sarah", "Mark", "Emma", "Chris", "Sophia", "Daniel", "Olivia"])
        eggs_sold = random.randint(30, 150)  # Random sales between 1-5 crates

        if total_sold + eggs_sold > eggs_produced + previous_remaining:
            break  # Stop if selling more than available

        EggSale.objects.create(
            date=date,
            buyer_name=buyer_name,
            eggs_sold=eggs_sold,
            amount_paid=eggs_sold * 20  # Assume ₦20 per egg
        )

        total_sold += eggs_sold  # Update daily sales count

    # ✅ Update eggs_sold & eggs_remaining in the production record
    record.eggs_sold = total_sold
    record.save()  # Trigger recalculation

print("✅ 3 months of egg production records successfully created!")
