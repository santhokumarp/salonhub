# booking/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from datetime import datetime,timedelta

from .models import CartItem, Booking, BookingService, RESERVATION_MINUTES
from .serializers import BookingSerializer, CreateBookingSerializer
from scheduler.models import DailySlot, SlotMaster
from services.models import Child_services
from booking.helpers import compute_required_slot_master_ids  # you indicated this exists


class CartAddView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        service_id = request.data.get("service_id")
        service = get_object_or_404(Child_services, id=service_id)

        item, created = CartItem.objects.get_or_create(user=request.user, service=service)
        if not created:
            item.quantity += 1
            item.save()

        return Response({"detail": "Service added to cart"}, status=201)


class CartView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        items = CartItem.objects.filter(user=request.user)
        ser = []  # reuse serializer as needed
        subtotal = sum([float(i.service.price) * i.quantity for i in items])
        gst = round(subtotal * 0.18, 2)
        grand_total = round(subtotal + gst, 2)

        return Response({
            "items": [{"service": i.service.id, "name": i.service.child_service_name, "qty": i.quantity} for i in items],
            "subtotal": subtotal,
            "gst": gst,
            "grand_total": grand_total
        })


# class CheckoutView(APIView):
#     """
#     POST payload:
#     {
#       "start_slot_id": 123,
#       "services": [{"service_id": 1}, {"service_id": 2}]
#     }
#     """
#     # permission_classes = [permissions.IsAuthenticated]

#     def post(self, request):
#         serializer = CreateBookingSerializer(data=request.data, context={'request': request})
#         serializer.is_valid(raise_exception=True)
#         start_slot_id = serializer.validated_data['start_slot_id']
#         services_list = serializer.validated_data['services']

#         # PRE-CHECK: get slot and required consecutive slots count depending on service durations
#         # total_minutes and compute_required_slot_master_ids() logic must exist in booking.helpers
#         cart_items = CartItem.objects.filter(user=request.user)
#         # If using Cart flow: compute total minutes from cart_items
#         total_minutes = 0
#         if cart_items.exists():
#             total_minutes = sum([ci.service.duration * ci.quantity for ci in cart_items])
#         else:
#             # If services provided explicitly, compute sum durations
#             for s in services_list:
#                 svc = Child_services.objects.get(id=s['service_id'])
#                 total_minutes += svc.duration

#         with transaction.atomic():
#             slot = DailySlot.objects.select_for_update().get(id=start_slot_id)

#             if slot.status != "available":
#                 return Response({"detail": "Selected slot not available"}, status=status.HTTP_400_BAD_REQUEST)

#             # compute required consecutive slot_master ids
#             slot_masters = SlotMaster.objects.filter(is_active=True).order_by("start_time")
#             needed_master_ids = compute_required_slot_master_ids(slot.slot_master, slot_masters, total_minutes)
#             if not needed_master_ids:
#                 return Response({"detail": "Not enough consecutive slots"}, status=status.HTTP_400_BAD_REQUEST)

#             # lock required daily slots
#             required_slots = list(
#                 DailySlot.objects.select_for_update().filter(
#                     slot_master_id__in=needed_master_ids,
#                     slot_date=slot.slot_date
#                 ).order_by('slot_master__start_time')
#             )

#             if len(required_slots) != len(needed_master_ids):
#                 return Response({"detail": "Required slots not all present"}, status=status.HTTP_400_BAD_REQUEST)

#             # ensure all are available
#             for ds in required_slots:
#                 if ds.status != 'available':
#                     return Response({"detail": "Some required slots are no longer available"}, status=status.HTTP_400_BAD_REQUEST)

#             # Reserve/book them as "booked" to prevent others; booking remains pending until admin confirms
#             for ds in required_slots:
#                 ds.status = 'booked'   # we use 'booked' to block others; revert on decline
#                 ds.booked_by = request.user
#                 # You can set booked_service to the first service for quick lookup (optional)
#                 if services_list:
#                     ds.booked_service = Child_services.objects.get(id=services_list[0]['service_id'])
#                 ds.save()

#             # Create Booking
#             booking = Booking.objects.create(
#                 user=request.user,
#                 start_slot=slot,
#                 status='pending'
#             )

#             # Create BookingService rows
#             if cart_items.exists():
#                 for ci in cart_items:
#                     BookingService.objects.create(booking=booking, service=ci.service)
#                 # clear cart
#                 cart_items.delete()
#             else:
#                 for s in services_list:
#                     svc = Child_services.objects.get(id=s['service_id'])
#                     BookingService.objects.create(booking=booking, service=svc)

#             # Calculate totals
#             booking.calculate_totals()

#         # Return confirmation payload
#         resp = {
#             "booking_id": booking.id,
#             "username": request.user.username,
#             "email": request.user.email,
#             "date": str(slot.slot_date),
#             "slot_time": f"{slot.slot_master.start_time} - {slot.slot_master.end_time}",
#             "status": booking.status
#         }
#         return Response(resp, status=status.HTTP_201_CREATED)



# --- Helper: compute required slot_master ids starting from a given slot_master
def compute_required_slot_master_ids(start_slot_master, ordered_slot_masters_qs, total_minutes):
    """
    Returns a list of slot_master IDs (consecutive) starting from start_slot_master
    that together cover >= total_minutes.
    ordered_slot_masters_qs must be queryset/list ordered by start_time.
    If not enough consecutive slots exist, returns empty list.
    """
    # Convert queryset to list to get index
    slot_masters = list(ordered_slot_masters_qs)
    try:
        start_index = next(i for i, sm in enumerate(slot_masters) if sm.id == start_slot_master.id)
    except StopIteration:
        return []

    accumulated = 0
    needed_ids = []
    for sm in slot_masters[start_index:]:
        # calculate duration in minutes between sm.start_time and sm.end_time
        # start_time/end_time are time objects, convert to datetime on same day
        dt_start = datetime.combine(datetime.today(), sm.start_time)
        dt_end = datetime.combine(datetime.today(), sm.end_time)
        duration = int((dt_end - dt_start).total_seconds() // 60)
        if duration <= 0:
            # fallback: assume 30 minutes if bad data
            duration = 30

        accumulated += duration
        needed_ids.append(sm.id)

        if accumulated >= total_minutes:
            return needed_ids

    # not enough consecutive slots
    return []

# --- Fixed CheckoutView
class CheckoutView(APIView):
    """
    POST payload:
    {
      "start_slot_id": 123,
      "services": [{"service_id": 1}, {"service_id": 2}]
    }

    This view requires JWT auth: add header
      Authorization: Bearer <access_token>
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        # Validate input payload via serializer
        serializer = CreateBookingSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        start_slot_id = serializer.validated_data['start_slot_id']
        services_list = serializer.validated_data.get('services', [])  # list of dicts with "service_id"

        # Determine total minutes required (from cart or from provided services)
        cart_items = CartItem.objects.filter(user=request.user)
        total_minutes = 0
        if cart_items.exists():
            # Cart-flow: sum durations (quantity assumed 1)
            for ci in cart_items.select_related('service'):
                total_minutes += int(ci.service.duration)
        else:
            # Explicit services provided in payload
            if not services_list:
                return Response({"detail": "No services provided and cart is empty."},
                                status=status.HTTP_400_BAD_REQUEST)
            for s in services_list:
                svc = Child_services.objects.filter(id=s.get('service_id')).first()
                if not svc:
                    return Response({"detail": f"Service {s.get('service_id')} not found."},
                                    status=status.HTTP_400_BAD_REQUEST)
                total_minutes += int(svc.duration)

        # Begin transactional booking/reservation
        try:
            with transaction.atomic():
                # Lock the start slot row
                try:
                    start_slot = DailySlot.objects.select_for_update().get(id=start_slot_id)
                except DailySlot.DoesNotExist:
                    return Response({"detail": "Start slot not found."}, status=status.HTTP_404_NOT_FOUND)

                # Check if start slot is available
                if start_slot.status != "available":
                    return Response({"detail": "Selected start slot not available."},
                                    status=status.HTTP_400_BAD_REQUEST)

                # Get ordered slot master list and compute required slot_master ids
                slot_masters = SlotMaster.objects.filter(is_active=True).order_by("start_time")
                needed_master_ids = compute_required_slot_master_ids(start_slot.slot_master, slot_masters, total_minutes)

                if not needed_master_ids:
                    return Response({"detail": "Not enough consecutive slots available for selected services."},
                                    status=status.HTTP_400_BAD_REQUEST)

                # Lock and fetch the corresponding DailySlot rows for the same date
                required_slots_qs = DailySlot.objects.select_for_update().filter(
                    slot_master_id__in=needed_master_ids,
                    slot_date=start_slot.slot_date
                ).order_by('slot_master__start_time')

                required_slots = list(required_slots_qs)

                # Ensure all required slots exist
                if len(required_slots) != len(needed_master_ids):
                    return Response({"detail": "Required slots for the selected date are not present."},
                                    status=status.HTTP_400_BAD_REQUEST)

                # Ensure all required slots are available
                for ds in required_slots:
                    if ds.status != 'available':
                        return Response({"detail": "Some required slots are no longer available."},
                                        status=status.HTTP_400_BAD_REQUEST)

                # Reserve (mark as booked/pending) these slots now to prevent race conditions
                for ds in required_slots:
                    ds.status = 'booked'
                    ds.booked_by = request.user
                    if services_list:
                        # set to first service for quick lookup
                        ds.booked_service = Child_services.objects.filter(id=services_list[0].get('service_id')).first()
                    ds.save()

                # Create Booking (belongs to authenticated user)
                booking = Booking.objects.create(
                    user=request.user,
                    start_slot=start_slot,
                    status='pending'
                )

                # Add BookingService items
                if cart_items.exists():
                    for ci in cart_items:
                        BookingService.objects.create(booking=booking, service=ci.service)
                    # clear cart
                    cart_items.delete()
                else:
                    for s in services_list:
                        svc = Child_services.objects.get(id=s.get('service_id'))
                        BookingService.objects.create(booking=booking, service=svc)

                # Calculate totals (uses Booking.calculate_totals())
                booking.calculate_totals()

        except Exception as exc:
            # Log if you have a logger; for now return 500 with safe message
            return Response({"detail": "Internal server error during booking.", "error": str(exc)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Success: return confirmation payload
        resp = {
            "booking_id": booking.id,
            "username": request.user.username,
            "email": request.user.email,
            "date": str(start_slot.slot_date),
            "slot_time": f"{start_slot.slot_master.start_time} - {start_slot.slot_master.end_time}",
            "status": booking.status
        }
        return Response(resp, status=status.HTTP_201_CREATED)




# ADMIN endpoints
class AdminAcceptView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request):
        booking_id = request.data.get("booking_id")
        booking = get_object_or_404(Booking, id=booking_id)

        if booking.status == 'confirmed':
            return Response({"detail": "Already confirmed"}, status=400)

        # find all slots required and set them to final booked state (they are already set to 'booked' above)
        # We assume the same compute_required_slot_master_ids helper to calculate the full set from booking.start_slot
        total_minutes = sum([bs.service.duration for bs in booking.services.all()])
        slot_masters = SlotMaster.objects.filter(is_active=True).order_by("start_time")
        needed = compute_required_slot_master_ids(booking.start_slot.slot_master, slot_masters, total_minutes)

        DailySlot.objects.filter(
            slot_master_id__in=needed,
            slot_date=booking.start_slot.slot_date
        ).update(
            status='booked',
            booked_by=booking.user,
            booked_service=booking.services.first().service if booking.services.exists() else None
        )

        booking.status = 'confirmed'
        booking.save(update_fields=['status'])

        # send confirmation email via signals or manually
        return Response({"detail": "Booking confirmed"}, status=200)


class AdminDeclineView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request):
        booking_id = request.data.get("booking_id")
        booking = get_object_or_404(Booking, id=booking_id)

        if booking.status in ('declined', 'cancelled'):
            return Response({"detail": "Booking already declined/cancelled"}, status=400)

        total_minutes = sum([bs.service.duration for bs in booking.services.all()])
        slot_masters = SlotMaster.objects.filter(is_active=True).order_by("start_time")
        needed = compute_required_slot_master_ids(booking.start_slot.slot_master, slot_masters, total_minutes)

        # Free slots: set to available and remove booked_by/booked_service
        slots_qs = DailySlot.objects.filter(
            slot_master_id__in=needed,
            slot_date=booking.start_slot.slot_date
        )
        for s in slots_qs:
            s.status = 'available'
            s.booked_by = None
            s.booked_service = None
            s.save()

        booking.status = 'declined'
        booking.save(update_fields=['status'])

        return Response({"detail": "Booking declined and slots freed"}, status=200)


class BookingHistoryView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        bookings = Booking.objects.filter(user=request.user).order_by('-created_at')
        ser = BookingSerializer(bookings, many=True)
        return Response(ser.data)
