#!/usr/bin/env python3
"""
Test script to verify Production Summary functionality.
This script can be run independently to test the production summary without Django server.
"""

import os
import sys
import django
from datetime import date, timedelta

# Add the project directory to Python path
sys.path.append('/Users/apple/Desktop/nathan/personal/OABSAV2')

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from records.models import DailyCrateEntry, EggProductionRecord, EggSale
from django.contrib.auth.models import User

def create_sample_data():
    """Create sample data for testing the production summary."""
    print("Creating sample data for September 2025...")
    
    # Create a test user
    user, created = User.objects.get_or_create(
        username='test_user', 
        defaults={'email': 'test@example.com'}
    )
    
    # Create sample DailyCrateEntry records for September 2025 with detailed remarks
    sample_entries = [
        {'date': date(2025, 9, 1), 'crates': 5, 'pieces': 10, 'remark': 'Morning collection - Layer A (Rhode Island Red) - Excellent health, good feed response'},
        {'date': date(2025, 9, 1), 'crates': 3, 'pieces': 5, 'remark': 'Afternoon collection - Layer B (Leghorn) - Consistent production'},
        {'date': date(2025, 9, 1), 'crates': 2, 'pieces': 8, 'remark': 'Evening collection - Layer C (Sussex) - New batch, adapting well'},
        {'date': date(2025, 9, 2), 'crates': 4, 'pieces': 8, 'remark': 'Daily collection - All layers healthy, weather favorable'},
        {'date': date(2025, 9, 2), 'crates': 2, 'pieces': 3, 'remark': 'Evening collection - Layer C (Sussex) - Good progress'},
        {'date': date(2025, 9, 3), 'crates': 6, 'pieces': 12, 'remark': 'High production day - Layer A (Rhode Island Red) - Excellent feed quality showing results'},
        {'date': date(2025, 9, 3), 'crates': 1, 'pieces': 2, 'remark': 'Layer B (Leghorn) - Some stress due to weather change'},
        {'date': date(2025, 9, 3), 'crates': 3, 'pieces': 6, 'remark': 'Layer C (Sussex) - Recovering well from transition'},
        {'date': date(2025, 9, 4), 'crates': 3, 'pieces': 6, 'remark': 'Lower production day - Weather change affected all layers'},
        {'date': date(2025, 9, 4), 'crates': 1, 'pieces': 1, 'remark': 'Layer C (Sussex) - Minimal production due to stress'},
        {'date': date(2025, 9, 5), 'crates': 7, 'pieces': 15, 'remark': 'Excellent production - All layers recovered well from weather stress'},
        {'date': date(2025, 9, 5), 'crates': 2, 'pieces': 4, 'remark': 'Layer A (Rhode Island Red) - Peak performance, optimal conditions'},
        {'date': date(2025, 9, 5), 'crates': 1, 'pieces': 3, 'remark': 'Layer B (Leghorn) - Back to normal production levels'},
    ]
    
    # Clear existing data for September 2025
    DailyCrateEntry.objects.filter(date__year=2025, date__month=9).delete()
    EggProductionRecord.objects.filter(date__year=2025, date__month=9).delete()
    EggSale.objects.filter(date__year=2025, date__month=9).delete()
    
    # Create DailyCrateEntry records
    for entry_data in sample_entries:
        DailyCrateEntry.objects.create(
            date=entry_data['date'],
            crates=entry_data['crates'],
            pieces=entry_data['pieces'],
            remark=entry_data['remark'],
            entered_by=user
        )
    
    # Create EggProductionRecord records with detailed production notes
    production_records = [
        {'date': date(2025, 9, 1), 'eggs_produced': 485, 'eggs_sold': 200, 'remark': 'Good start to the month - All layers performing well'},
        {'date': date(2025, 9, 2), 'eggs_produced': 285, 'eggs_sold': 150, 'remark': 'Steady production - Consistent with expectations'},
        {'date': date(2025, 9, 3), 'eggs_produced': 392, 'eggs_sold': 300, 'remark': 'High production day - Excellent feed quality showing results'},
        {'date': date(2025, 9, 4), 'eggs_produced': 96, 'eggs_sold': 50, 'remark': 'Lower production - Weather change affected layer performance'},
        {'date': date(2025, 9, 5), 'eggs_produced': 225, 'eggs_sold': 100, 'remark': 'Recovery day - Layers adapting to weather changes'},
    ]
    
    for record_data in production_records:
        EggProductionRecord.objects.create(
            date=record_data['date'],
            eggs_produced=record_data['eggs_produced'],
            eggs_sold=record_data['eggs_sold'],
            remark=record_data['remark']
        )
    
    # Create some sample sales
    sales_data = [
        {'date': date(2025, 9, 1), 'buyer_name': 'John Doe', 'eggs_sold': 200, 'amount_paid': 2000.00},
        {'date': date(2025, 9, 2), 'buyer_name': 'Jane Smith', 'eggs_sold': 150, 'amount_paid': 1500.00},
        {'date': date(2025, 9, 3), 'buyer_name': 'Bob Johnson', 'eggs_sold': 300, 'amount_paid': 3000.00},
        {'date': date(2025, 9, 4), 'buyer_name': 'Alice Brown', 'eggs_sold': 50, 'amount_paid': 500.00},
        {'date': date(2025, 9, 5), 'buyer_name': 'Charlie Wilson', 'eggs_sold': 100, 'amount_paid': 1000.00},
    ]
    
    for sale_data in sales_data:
        EggSale.objects.create(
            date=sale_data['date'],
            buyer_name=sale_data['buyer_name'],
            eggs_sold=sale_data['eggs_sold'],
            amount_paid=sale_data['amount_paid']
        )
    
    print("✅ Sample data created successfully!")
    return True

def test_production_summary_calculations():
    """Test the production summary calculations."""
    print("\nTesting production summary calculations...")
    
    # Get all DailyCrateEntry records for September 2025
    daily_entries = DailyCrateEntry.objects.filter(
        date__year=2025, 
        date__month=9
    ).order_by('date', 'id')
    
    # Get all EggProductionRecord records for the same period
    production_records = EggProductionRecord.objects.filter(
        date__year=2025, 
        date__month=9
    ).order_by('date')
    
    # Create a comprehensive summary
    summary_data = []
    previous_day_total = 0
    
    # Get all unique dates in the month
    all_dates = set()
    for entry in daily_entries:
        all_dates.add(entry.date)
    for record in production_records:
        all_dates.add(record.date)
    
    all_dates = sorted(all_dates)
    
    print(f"Found {len(all_dates)} unique dates with data")
    
    for current_date in all_dates:
        # Get all entries for this date
        date_entries = daily_entries.filter(date=current_date)
        
        # Calculate totals for this date
        total_crates = sum(entry.crates for entry in date_entries)
        total_pieces = sum(entry.pieces for entry in date_entries)
        total_eggs = (total_crates * 30) + total_pieces
        
        # Get production record for this date
        production_record = production_records.filter(date=current_date).first()
        
        # Get sales for this date
        sales = EggSale.objects.filter(date=current_date)
        total_sold = sum(sale.eggs_sold for sale in sales)
        
        # Calculate percentage change from previous day
        percentage_change = 0
        if previous_day_total > 0:
            percentage_change = ((total_eggs - previous_day_total) / previous_day_total) * 100
        
        # Get all remarks for this date
        remarks = [entry.remark for entry in date_entries if entry.remark]
        
        # Get users who entered data
        users = [entry.entered_by.username if entry.entered_by else 'Unknown' for entry in date_entries]
        
        summary_data.append({
            'date': current_date,
            'entries': date_entries,
            'total_crates': total_crates,
            'total_pieces': total_pieces,
            'total_eggs': total_eggs,
            'production_record': production_record,
            'total_sold': total_sold,
            'percentage_change': percentage_change,
            'remarks': remarks,
            'users': users,
            'sales': sales,
        })
        
        # Update previous day total for next iteration
        previous_day_total = total_eggs
    
    # Calculate monthly totals
    monthly_total_crates = sum(item['total_crates'] for item in summary_data)
    monthly_total_pieces = sum(item['total_pieces'] for item in summary_data)
    monthly_total_eggs = sum(item['total_eggs'] for item in summary_data)
    monthly_total_sold = sum(item['total_sold'] for item in summary_data)
    
    # Calculate average daily production
    days_with_data = len([item for item in summary_data if item['total_eggs'] > 0])
    average_daily_production = monthly_total_eggs / days_with_data if days_with_data > 0 else 0
    
    print(f"\n📊 Production Summary for September 2025:")
    print(f"Total Crates: {monthly_total_crates}")
    print(f"Total Pieces: {monthly_total_pieces}")
    print(f"Total Eggs: {monthly_total_eggs}")
    print(f"Total Sold: {monthly_total_sold}")
    print(f"Average Daily Production: {average_daily_production:.0f} eggs")
    print(f"Days with Data: {days_with_data}")
    
    print(f"\n📅 Daily Breakdown:")
    for item in summary_data:
        change_indicator = ""
        if item['percentage_change'] > 0:
            change_indicator = f"📈 +{item['percentage_change']:.1f}%"
        elif item['percentage_change'] < 0:
            change_indicator = f"📉 {item['percentage_change']:.1f}%"
        else:
            change_indicator = "🆕 First day"
        
        print(f"  {item['date']}: {item['total_eggs']} eggs ({item['total_crates']} crates, {item['total_pieces']} pieces) {change_indicator}")
    
    return summary_data

if __name__ == "__main__":
    try:
        print("🚀 Testing Production Summary Functionality")
        print("=" * 50)
        
        # Create sample data
        create_sample_data()
        
        # Test calculations
        summary_data = test_production_summary_calculations()
        
        print(f"\n✅ Production summary test completed successfully!")
        print(f"📊 Generated summary for {len(summary_data)} days")
        print(f"🌐 You can now visit: http://localhost:8000/production-summary/2025/9/")
        
    except Exception as e:
        print(f"❌ Production summary test failed: {e}")
        import traceback
        traceback.print_exc()
