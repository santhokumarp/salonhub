from django.db import transaction
from django.utils import timezone
from datetime import timedelta
from .models import Booking, BookingService, BookingSlot, CartItem, RESERVATION_MINUTES
from scheduler.models import DailySlot
from django.core.mail import send_mail
from django.conf import settings


def _get_slot_and_lock(slot_id):
    """
    Lock a slot row to prevent race conditions.
    Assumes DailySlot model defines STATUS_* constants.
    """
    return DailySlot.objects.select_for_update().get(id=slot_id)


def reserve_slot(slot_id, user):
    """
    Mark a slot as RESERVED for this user (temporary).
    """
    with transaction.atomic():
        slot = _get_slot_and_lock(slot_id)

        if getattr(slot, "status", None) != getattr(DailySlot, "STATUS_AVAILABLE", "available"):
            raise ValueError("Slot is not available")

        slot.status = getattr(DailySlot, "STATUS_RESERVED", "reserved")
        # If your DailySlot has reserved_by/reserved_at fields, set them:
        if hasattr(slot, "reserved_by"):
            slot.reserved_by = user
        if hasattr(slot, "reserved_at"):
            slot.reserved_at = timezone.now()
        slot.save()
    return slot


def _book_slot(slot, user):
    """
    Internal: set slot to BOOKED and set booked metadata if model supports it.
    """
    slot.status = getattr(DailySlot, "STATUS_BOOKED", "booked")
    if hasattr(slot, "booked_by"):
        slot.booked_by = user
    if hasattr(slot, "booked_at"):
        slot.booked_at = timezone.now()
    slot.save()
    return slot


def create_booking_single_service(user, slot_id, service_id, quantity=1, gst_percent=18):
    """
    For single-service flow: user picks service -> selects one slot -> create booking.
    - Locks and books the slot atomically.
    - Creates Booking, BookingService, BookingSlot, calculates totals.
    """
    with transaction.atomic():
        slot = _get_slot_and_lock(slot_id)
        if getattr(slot, "status", None) not in (getattr(DailySlot, "STATUS_AVAILABLE", "available"),
                                                 getattr(DailySlot, "STATUS_RESERVED", "reserved")):
            raise ValueError("Slot not available")

        # Book the slot
        _book_slot(slot, user)

        # Create booking
        # import inside to avoid circular imports
        from services.models import Child_services
        service = Child_services.objects.get(id=service_id)

        booking = Booking.objects.create(
            user=user,
            type=Booking.BOOKING_TYPE_SINGLE,
            selected_date=slot.date,
            gst_percent=gst_percent
        )

        BookingService.objects.create(
            booking=booking,
            service=service,
            price=service.price,
            duration=service.duration,
            quantity=quantity
        )

        BookingSlot.objects.create(booking=booking, slot=slot)

        booking.calculate_totals()
    # Send notification to admin (optional)
    return booking


def create_booking_from_cart(user, selected_date, slot_ids, gst_percent=18):
    """
    For multi-service (cart) flow:
    - `slot_ids` should be list of slot ids chosen by the user.
    - Number of slots must match total quantity of items in the user's cart (sum quantities).
    - Atomic: lock all selected slots with select_for_update.
    - Mark them booked, create booking + service snapshots + BookingSlots.
    """
    from services.models import Child_services

    cart_items = list(CartItem.objects.filter(user=user).select_related("service"))
    if not cart_items:
        raise ValueError("Cart is empty")

    total_required_slots = sum([c.quantity for c in cart_items])
    if len(slot_ids) != total_required_slots:
        raise ValueError(f"You selected {len(slot_ids)} slots but {total_required_slots} slots are required")

    with transaction.atomic():
        # Lock selected slots
        slots = list(DailySlot.objects.select_for_update().filter(id__in=slot_ids))

        if len(slots) != len(slot_ids):
            raise ValueError("One or more selected slots not found")

        # Validate all slots are on selected_date and available or reserved
        for s in slots:
            if s.date != selected_date:
                raise ValueError("All selected slots must match the selected date")
            if getattr(s, "status", None) not in (getattr(DailySlot, "STATUS_AVAILABLE", "available"),
                                                 getattr(DailySlot, "STATUS_RESERVED", "reserved")):
                raise ValueError(f"Slot {s.id} is not available")

        # Book the slots
        for s in slots:
            _book_slot(s, user)

        # Create booking
        booking = Booking.objects.create(user=user, type=Booking.BOOKING_TYPE_MULTIPLE, selected_date=selected_date, gst_percent=gst_percent)

        # Create BookingService entries (snapshot)
        for c in cart_items:
            BookingService.objects.create(
                booking=booking,
                service=c.service,
                price=c.service.price,
                duration=c.service.duration,
                quantity=c.quantity
            )

        # Create BookingSlot entries (one row for each slot chosen)
        for s in slots:
            BookingSlot.objects.create(booking=booking, slot=s)

        # Clear user's cart
        CartItem.objects.filter(user=user).delete()

        # Calculate totals
        booking.calculate_totals()

    return booking


def admin_accept_booking(booking_id, admin_user=None, notify=True):
    """
    Admin accepts booking: set booking.status to confirmed and optionally send email.
    """
    booking = Booking.objects.get(id=booking_id)
    booking.status = Booking.STATUS_CONFIRMED
    booking.save(update_fields=["status"])
    if notify:
        _send_user_notification(booking, accepted=True)
    return booking


def admin_decline_booking(booking_id, admin_note=None, notify=True):
    """
    Admin declines booking: set booking.status to declined, free slots, notify user
    """
    booking = Booking.objects.get(id=booking_id)
    booking.status = Booking.STATUS_DECLINED
    booking.admin_note = admin_note
    booking.save(update_fields=["status", "admin_note"])

    # free allocated slots
    for bs in booking.slots.all():
        s = bs.slot
        s.status = getattr(DailySlot, "STATUS_AVAILABLE", "available")
        if hasattr(s, "reserved_by"):
            s.reserved_by = None
        if hasattr(s, "reserved_at"):
            s.reserved_at = None
        if hasattr(s, "booked_by"):
            s.booked_by = None
        if hasattr(s, "booked_at"):
            s.booked_at = None
        s.save()

    if notify:
        _send_user_notification(booking, accepted=False)
    return booking


def _send_user_notification(booking, accepted: bool):
    """
    Simple email helper. Uses Django's send_mail; configure settings.EMAIL_*
    """
    subject = f"Your booking #{booking.id} - {'Confirmed' if accepted else 'Declined'}"
    if accepted:
        body = f"Hello {booking.user},\n\nYour booking #{booking.id} has been confirmed.\n\nThanks."
    else:
        body = f"Hello {booking.user},\n\nYour booking #{booking.id} has been declined.\n\nNote: {booking.admin_note or 'No reason provided.'}\n\nPlease contact support if needed."

    send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [booking.user.email], fail_silently=True)

