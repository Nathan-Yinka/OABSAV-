from django.shortcuts import render, redirect, get_object_or_404
from .models import EggProductionRecord, EggSale
from .forms import EggProductionRecordForm, EggSaleForm
from django.utils.timezone import now
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Sum
from django.http import JsonResponse

def list_records(request):
    """Display filtered & paginated records with correct carry-over, using manual stock if available."""
    today = now().date()
    today_exists = EggProductionRecord.objects.filter(date=today).exists()

    try:
        # Get selected month & year from request (default to current)
        selected_month = int(request.GET.get('month', today.month))
        selected_year = int(request.GET.get('year', today.year))

        # Get the last record of the previous month (if available)
        previous_record = EggProductionRecord.objects.filter(
            date__lt=f"{selected_year}-{selected_month:02d}-01"
        ).order_by('-date').first()

        # ✅ Start with the manually entered stock if available, otherwise use eggs_remaining
        previous_remaining = (
            previous_record.manual_stock_entry
            if previous_record and previous_record.manual_stock_entry is not None
            else previous_record.eggs_remaining if previous_record else 0
        )

        # Get all records for the selected month & year
        records = EggProductionRecord.objects.filter(
            date__year=selected_year, date__month=selected_month
        ).order_by('date')

        processed_records = []

        for record in records:
            # ✅ Store previous day's remaining eggs, using manual stock if available
            record.previous_remaining = previous_remaining
            record.previous_remaining_crates = previous_remaining // 30
            record.previous_remaining_pieces = previous_remaining % 30

            # ✅ Total eggs available for the day (Produced + Previous Day's Remaining)
            total_available = previous_remaining + record.eggs_produced
            record.produced_crates = record.eggs_produced // 30
            record.produced_pieces = record.eggs_produced % 30

            # ✅ Get total eggs sold today
            total_sold_today = EggSale.objects.filter(date=record.date).aggregate(
                total=Sum('eggs_sold')
            )['total'] or 0

            record.eggs_sold = total_sold_today
            record.sold_crates = total_sold_today // 30
            record.sold_pieces = total_sold_today % 30

            # ✅ Correct calculation of remaining eggs
            remaining_eggs = total_available - total_sold_today
            record.remaining = remaining_eggs
            record.remaining_crates = remaining_eggs // 30
            record.remaining_pieces = remaining_eggs % 30

            # ✅ **Update `eggs_remaining` in the database**
            record.eggs_remaining = remaining_eggs
            record.save(update_fields=["eggs_remaining"])  # ✅ Save updated value to DB

            # ✅ Attach sales for this record
            record.sales = EggSale.objects.filter(date=record.date)
            record.sales_data = []
            for sale in record.sales:
                sale.sold_crates = sale.eggs_sold // 30
                sale.sold_pieces = sale.eggs_sold % 30
                record.sales_data.append(sale)

            # ✅ Calculate Audit Discrepancy (Convert to Crates & Pieces)
            if record.manual_stock_entry is not None:
                audit_discrepancy = record.manual_stock_entry - record.remaining
                record.audit_discrepancy_crates = abs(audit_discrepancy) // 30  # Get full crates
                record.audit_discrepancy_pieces = abs(audit_discrepancy) % 30  # Get remaining pieces
                record.audit_discrepancy_value = audit_discrepancy  # Store original value for UI handling
            else:
                record.audit_discrepancy_crates = None
                record.audit_discrepancy_pieces = None
                record.audit_discrepancy_value = None

            # ✅ Carry over manually entered stock for next day if available
            previous_remaining = (
                record.manual_stock_entry if record.manual_stock_entry is not None else record.remaining
            )

            # ✅ Add processed record to the list
            processed_records.append(record)

        # ✅ Reverse the list to show the most recent record first
        processed_records.reverse()

        # ✅ Paginate records (10 per page)
        paginator = Paginator(processed_records, 33)
        page_number = request.GET.get('page')
        paginated_records = paginator.get_page(page_number)

        # ✅ Success message when records are loaded
        # messages.success(request, f"Records for {selected_month}/{selected_year} loaded successfully!")

    except Exception as e:
        messages.error(request, f"Error loading records: {str(e)}")
        paginated_records = []

    # Generate month & year options
    years = range(today.year - 5, today.year + 1)  # Last 5 years
    months = [
        (1, "January"), (2, "February"), (3, "March"), (4, "April"), 
        (5, "May"), (6, "June"), (7, "July"), (8, "August"), 
        (9, "September"), (10, "October"), (11, "November"), (12, "December")
    ]

    return render(request, 'records_list.html', {
        'records': paginated_records,
        'today_exists': today_exists,
        'today': today,
        'selected_month': selected_month,
        'selected_year': selected_year,
        'months': months,
        'years': years
    })


def update_manual_stock(request, record_id):
    """Update manual stock entry for a specific record and return updated eggs_remaining & audit discrepancy."""
    if request.method == "POST":
        record = get_object_or_404(EggProductionRecord, id=record_id)

        # Get crates & pieces input (default to 0 if empty)
        crates = request.POST.get("manual_stock_crates", 0)
        pieces = request.POST.get("manual_stock_pieces", 0)

        try:
            crates = int(crates)
            pieces = int(pieces)
            manual_stock_entry = (crates * 30) + pieces  # Convert to total pieces

            # ✅ Fetch previous day's record
            previous_record = EggProductionRecord.objects.filter(date__lt=record.date).order_by('-date').first()
            previous_remaining = (
                previous_record.manual_stock_entry if previous_record and previous_record.manual_stock_entry is not None
                else previous_record.eggs_remaining if previous_record else 0
            )

            # ✅ Get total eggs sold today
            total_sold_today = EggSale.objects.filter(date=record.date).aggregate(
                total=Sum('eggs_sold')
            )['total'] or 0

            # ✅ Correct calculation of `eggs_remaining`
            new_eggs_remaining = (record.eggs_produced + previous_remaining) - total_sold_today

            # ✅ Save updated values
            record.manual_stock_entry = manual_stock_entry
            record.eggs_remaining = new_eggs_remaining  # ✅ Update eggs_remaining in DB
            record.save(update_fields=["manual_stock_entry", "eggs_remaining"])

            # ✅ Correct calculation for `audit_discrepancy`
            audit_discrepancy = manual_stock_entry - new_eggs_remaining
            audit_discrepancy_crates = abs(audit_discrepancy) // 30  # Get full crates
            audit_discrepancy_pieces = abs(audit_discrepancy) % 30  # Get remaining pieces

            # ✅ Add success message
            # messages.success(request, f"Stock updated successfully! Audit discrepancy: {audit_discrepancy_crates} crates, {audit_discrepancy_pieces} pieces.")

            # ✅ Return updated values to frontend
            return JsonResponse({
                "success": True,
                "manual_stock_entry": manual_stock_entry,
                "manual_stock_crates": record.manual_stock_crates,
                "manual_stock_pieces": record.manual_stock_pieces,
                "eggs_remaining": new_eggs_remaining,  # ✅ Return updated eggs_remaining
                "audit_discrepancy_value": audit_discrepancy,  # Raw value
                "audit_discrepancy_crates": audit_discrepancy_crates,
                "audit_discrepancy_pieces": audit_discrepancy_pieces,
                # "messages": list(messages.get_messages(request))  # ✅ Send messages to frontend
            })

        except ValueError:
            messages.error(request, "Invalid input! Please enter valid numbers.")
            return JsonResponse({"success": False, "error": "Invalid input"})

    messages.error(request, "Invalid request method.")
    return JsonResponse({"success": False, "error": "Invalid request"})



def add_record(request):
    """Add a new egg production record for today, carrying forward remaining eggs from yesterday."""
    today = now().date()

    # Prevent duplicate entries for today
    if EggProductionRecord.objects.filter(date=today).exists():
        messages.error(request, "Today's record already exists!")
        return redirect('records_list')

    # Fetch previous day's remaining eggs
    previous_record = EggProductionRecord.objects.filter(date__lt=today).order_by('-date').first()
    previous_remaining = previous_record.eggs_remaining if previous_record else 0

    if request.method == 'POST':
        form = EggProductionRecordForm(request.POST)
        if form.is_valid():
            record = form.save(commit=False)
            record.date = today  # Auto-assign today's date
            record.save()  # ✅ Do NOT modify `eggs_produced`

            # ✅ Add success message
            messages.success(request, "Egg production record for today has been added successfully!")
            return redirect('records_list')
        else:
            non_field_errors = form.non_field_errors()
            if non_field_errors:
                for error in non_field_errors:
                    messages.error(request, error)  # Display as Toastify messages

            # ✅ Extract field-specific errors and show in Toastify
            for field, errors in form.errors.items():
                if field != "__all__":  # Skip non-field errors (already handled)
                    for error in errors:
                        messages.error(request, f"{field.capitalize()}: {error}")

    else:
        form = EggProductionRecordForm()

    return render(request, 'record_form.html', {'form': form, 'previous_remaining': previous_remaining})



def edit_record(request, record_id):
    """Edit an existing egg production record."""
    record = get_object_or_404(EggProductionRecord, pk=record_id)
    
    if request.method == 'POST':
        form = EggProductionRecordForm(request.POST, instance=record)
        if form.is_valid():
            updated_record = form.save(commit=False)
            updated_record.eggs_sold = sum(sale.eggs_sold for sale in EggSale.objects.filter(date=record.date))

            # ✅ Preserve `manual_stock_entry` if it's missing from the form
            if 'manual_stock_entry' not in form.cleaned_data:
                updated_record.manual_stock_entry = record.manual_stock_entry

            updated_record.save()

            # ✅ Add success message
            messages.success(request, "Record updated successfully!")
            return redirect('records_list')
        else:
            non_field_errors = form.non_field_errors()
            if non_field_errors:
                for error in non_field_errors:
                    messages.error(request, error)  # Display as Toastify messages

            # ✅ Extract field-specific errors and show in Toastify
            for field, errors in form.errors.items():
                if field != "__all__":  # Skip non-field errors (already handled)
                    for error in errors:
                        messages.error(request, f"{field.capitalize()}: {error}")
    
    else:
        form = EggProductionRecordForm(instance=record)

    return render(request, 'record_form.html', {'form': form, 'edit': True})


def add_sale(request):
    """Add a new egg sale and update the corresponding production record."""
    today = now().date()
    production_record = EggProductionRecord.objects.filter(date=today).first()

    if not production_record:
        messages.error(request, "No egg production record found for today. Please add today's production record first.")
        return redirect('records_list')

    if request.method == 'POST':
        form = EggSaleForm(request.POST)
        if form.is_valid():
            sale = form.save(commit=False)
            sale.date = today  # Auto-set today's date
            sale.save()
            
            # ✅ Recalculate total eggs sold for today
            production_record.eggs_sold = sum(s.eggs_sold for s in EggSale.objects.filter(date=today))
            production_record.save()

            # ✅ Success Message
            messages.success(request, "Sale recorded successfully!")
            return redirect('records_list')
        else:
            # ✅ Extract non-field errors properly
            non_field_errors = form.non_field_errors()
            if non_field_errors:
                for error in non_field_errors:
                    messages.error(request, error)  # Display as Toastify messages

            # ✅ Extract field-specific errors and show in Toastify
            for field, errors in form.errors.items():
                if field != "__all__":  # Skip non-field errors (already handled)
                    for error in errors:
                        messages.error(request, f"{field.capitalize()}: {error}")

    else:
        form = EggSaleForm()

    return render(request, 'sale_form.html', {'form': form})


def edit_sale(request, sale_id):
    """Edit an existing egg sale."""
    sale = get_object_or_404(EggSale, pk=sale_id)
    production_record = EggProductionRecord.objects.filter(date=sale.date).first()

    if request.method == 'POST':
        form = EggSaleForm(request.POST, instance=sale)
        if form.is_valid():
            updated_sale = form.save()

            # ✅ Recalculate total eggs sold for the day
            if production_record:
                production_record.eggs_sold = sum(s.eggs_sold for s in EggSale.objects.filter(date=sale.date))
                production_record.save()

            # ✅ Success Message
            messages.success(request, "Sale updated successfully!")
            return redirect('records_list')
        else:
            non_field_errors = form.non_field_errors()
            if non_field_errors:
                for error in non_field_errors:
                    messages.error(request, error)  # Display as Toastify messages

            # ✅ Extract field-specific errors and show in Toastify
            for field, errors in form.errors.items():
                if field != "__all__":  # Skip non-field errors (already handled)
                    for error in errors:
                        messages.error(request, f"{field.capitalize()}: {error}")

    else:
        form = EggSaleForm(instance=sale)

    return render(request, 'sale_form.html', {'form': form, 'edit': True})
