from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from django.db import transaction
from .models import SlotMaster, DailySlot, WorkingDay, Holiday


@shared_task
def generate_rolling_slots():
    """
    AUTO GENERATION SYSTEM
    — Today
    — Tomorrow
    — Day After Tomorrow
    --------------------------------
    DailySlots = AUTO ONLY
    Admin creates ONLY SlotMaster
    """
    
    today = timezone.localdate()
    day1 = today
    day2 = today + timedelta(days=1)
    day3 = today + timedelta(days=2)

    valid_dates = [day1, day2, day3]

    # Step 1: Delete old days
    DailySlot.objects.exclude(slot_date__in=valid_dates).delete()

    # Step 2: Create missing days
    for date in valid_dates:
        if DailySlot.objects.filter(slot_date=date).exists():
            continue
        
        # Holiday check
        is_holiday = Holiday.objects.filter(holiday_date=date).exists()

        # Working day check
        weekday = date.weekday()
        wd = WorkingDay.objects.filter(weekday=weekday).first()
        is_closed = (wd and not wd.is_working)

        default_status = "blocked" if (is_holiday or is_closed) else "available"

        masters = SlotMaster.objects.filter(is_active=True)

        with transaction.atomic():
            for sm in masters:
                DailySlot.objects.create(
                    slot_master=sm,
                    slot_date=date,
                    status=default_status
                )

    return "Rolling 3-day slots created successfully."


