from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from django.db import transaction
from .models import SlotMaster, DailySlot, WorkingDay, Holiday


@shared_task
def generate_rolling_slots():
    """
    Maintain ONLY these 3 days:
    - today
    - tomorrow
    - day after tomorrow

    Delete ALL previous days permanently (yesterday and older).
    """

    today = timezone.localdate()
    tomorrow = today + timedelta(days=1)
    day_after_tomorrow = today + timedelta(days=2)

    valid_dates = [today, tomorrow, day_after_tomorrow]

    # STEP 1: DELETE ALL PAST DAYS (yesterday and older)
    DailySlot.objects.filter(slot_date__lt=today).delete()

    masters = SlotMaster.objects.filter(is_active=True)

    # STEP 2: Create missing slots ONLY for valid days for EACH SlotMaster
    for date in valid_dates:

        # ================================
        # HOLIDAY CHECK (FIXED)
        # ================================
        is_holiday = Holiday.objects.filter(date=date).exists()

        # ================================
        # WORKING DAY CHECK
        # ================================
        weekday = date.weekday()  # 0 = Monday ... 6 = Sunday
        wd = WorkingDay.objects.filter(weekday=weekday).first()
        is_closed = (wd and not wd.is_working)

        # ================================
        # DEFAULT SLOT STATUS
        # ================================
        if is_holiday:
            default_status = "blocked"
        elif is_closed:
            default_status = "blocked"
        else:
            default_status = "available"

        with transaction.atomic():
            for sm in masters:

                # Prevent duplicate slots for the same SlotMaster + date
                if DailySlot.objects.filter(slot_master=sm, slot_date=date).exists():
                    continue

                DailySlot.objects.create(
                    slot_master=sm,
                    slot_date=date,
                    status=default_status,
                    is_holiday=is_holiday
                )

    return "SUCCESS: Slots refreshed for today, tomorrow, and day-after-tomorrow."








