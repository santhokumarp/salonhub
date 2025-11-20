# scheduler/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta

from .models import SlotMaster, DailySlot, Holiday, WorkingDay


def _is_closed(date):
    if Holiday.objects.filter(holiday_date=date).exists():
        return True
    wd = WorkingDay.objects.filter(weekday=date.weekday()).first()
    return bool(wd and not wd.is_working)


@receiver(post_save, sender=SlotMaster)
def create_initial_dailyslots(sender, instance, created, **kwargs):
    """
    When a new SlotMaster is created → auto-generate DailySlots
    for today, tomorrow, and day after tomorrow (get_or_create).
    """
    if not created:
        return

    today = timezone.localdate()
    dates = [today, today + timedelta(days=1), today + timedelta(days=2)]

    for d in dates:
        status = "blocked" if _is_closed(d) else "available"
        DailySlot.objects.get_or_create(
            slot_master=instance,
            slot_date=d,
            defaults={"status": status}
        )


@receiver(post_save, sender=SlotMaster)
def create_or_update_dailyslots(sender, instance, created, **kwargs):
    """
    When a SlotMaster is created or updated → create/update DailySlots
    for today, tomorrow, day after.
    """

    today = timezone.localdate()
    dates = [today, today + timedelta(days=1), today + timedelta(days=2)]

    for date in dates:
        is_closed = _is_closed(date)
        status = "blocked" if is_closed else "available"

        obj, created_flag = DailySlot.objects.get_or_create(
            slot_master=instance,
            slot_date=date,
            defaults={"status": status}
        )

        # Update status if slot template changed
        if not created_flag:
            if obj.status != "booked":  # do NOT touch booked slots
                obj.status = status
                obj.save()

@receiver(post_save, sender=SlotMaster)
def create_slots_for_new_master(sender, instance, created, **kwargs):
    if not created:
        return

    today = timezone.localdate()
    tomorrow = today + timedelta(days=1)
    day_after_tomorrow = today + timedelta(days=2)

    valid_dates = [today, tomorrow, day_after_tomorrow]

    for date in valid_dates:

        # Do NOT create yesterday or past days
        if date < today:
            continue

        # Do NOT recreate if slot exists for this master+date
        if DailySlot.objects.filter(slot_master=instance, slot_date=date).exists():
            continue

        # Holiday check
        is_holiday = Holiday.objects.filter(holiday_date=date).exists()

        # Working day check
        weekday = date.weekday()
        wd = WorkingDay.objects.filter(weekday=weekday).first()
        is_closed = (wd and not wd.is_working)

        default_status = "blocked" if (is_holiday or is_closed) else "available"

        DailySlot.objects.create(
            slot_master=instance,
            slot_date=date,
            status=default_status
        )
