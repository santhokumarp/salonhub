# scheduler/slot_reset.py

from django.utils.timezone import now
from services.models import Slot   # make sure Slot model is inside services app

_last_reset_date = None


def auto_reset_slots():
    """
    Automatically resets booked slots every midnight.
    - Booked → Available
    - Past dates → Completed
    """
    global _last_reset_date
    today = now().date()

    # If already reset today, do nothing
    if _last_reset_date == today:
        return

    # Reset all slots: booked → available
    Slot.objects.filter(status="booked").update(status="available")

    # Mark past slots as completed
    Slot.objects.filter(date__lt=today).update(status="completed")

    # Save today's date to avoid repeating
    _last_reset_date = today

    print("Slots automatically reset for:", today)
