# booking/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Count
from datetime import datetime,timedelta
from django.db.models import Sum
from decimal import Decimal
from .models import CartItem, Booking, BookingService, RESERVATION_MINUTES,AdminNotification
from .serializers import BookingSerializer, CreateBookingSerializer
from scheduler.models import DailySlot, SlotMaster
from services.models import Child_services
from django.db.models.functions import TruncMonth
from booking.helpers import compute_required_slot_master_ids  # you indicated this exists



class CartAddView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, service_id):
        # Validate service exists
        try:
            service = Child_services.objects.get(id=service_id)
        except Child_services.DoesNotExist:
            return Response({"detail": f"Child service {service_id} not found"}, status=404)

        # Add or increase quantity
        item, created = CartItem.objects.get_or_create(
            user=request.user,
            service=service
        )

        if not created:
            item.quantity += 1
            item.save()

        return Response({
            "detail": f"{service.child_service_name} added to cart",
            "service_id": service.id,
            "quantity": item.quantity
        }, status=201)




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

def create_admin_notification(booking):
    """
    Creates a notification entry for admins when a new booking is made.
    """
    message = f" New Booking #{booking.id} by {booking.user.username} on {booking.start_slot.slot_date}"

    AdminNotification.objects.create(
        booking=booking,
        message=message
    )

# --- Fixed CheckoutView
class CheckoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        booking = Booking.objects.filter(user=request.user).order_by('-created_at').first()

        if not booking:
              return Response({"detail": "No booking found"}, status=404)

        serializer = BookingSerializer(booking)
        return Response(serializer.data, status=200)

    def post(self, request):
        serializer = CreateBookingSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        start_slot_id = serializer.validated_data["start_slot_id"]
        services_list = serializer.validated_data["services"]

        # Calculate total required minutes
        cart_items = CartItem.objects.filter(user=request.user)
        total_minutes = 0

        if cart_items.exists():
            for ci in cart_items:
                total_minutes += int(ci.service.duration)
        else:
            for s in services_list:
                service = Child_services.objects.get(id=s["service_id"])
                total_minutes += int(service.duration)

        try:
            with transaction.atomic():
                start_slot = DailySlot.objects.select_for_update().get(id=start_slot_id)

                if start_slot.status != "available":
                    return Response({"detail": "Start slot not available"}, status=400)

                slot_masters = SlotMaster.objects.filter(is_active=True).order_by("start_time")
                needed_master_ids = compute_required_slot_master_ids(
                    start_slot.slot_master,
                    slot_masters,
                    total_minutes,
                )

                if not needed_master_ids:
                    return Response({"detail": "Not enough consecutive slots"}, status=400)

                required_slots = list(
                    DailySlot.objects.select_for_update()
                    .filter(slot_master_id__in=needed_master_ids, slot_date=start_slot.slot_date)
                    .order_by("slot_master__start_time")
                )

                for s in required_slots:
                    if s.status != "available":
                        return Response({"detail": "Some slots already booked"}, status=400)

                # Reserve slots
                for s in required_slots:
                    s.status = "booked"
                    s.booked_by = request.user
                    s.booked_service = Child_services.objects.get(
                        id=services_list[0]["service_id"]
                    )
                    s.save()

                # Create Booking
                booking = Booking.objects.create(
                    user=request.user,
                    start_slot=start_slot,
                    status="pending",
                )

                # Save booking services
                saved_services = []
                if cart_items.exists():
                    for ci in cart_items:
                        BookingService.objects.create(booking=booking, service=ci.service)
                        saved_services.append(ci.service.child_service_name)
                    cart_items.delete()
                else:
                    for s in services_list:
                        service = Child_services.objects.get(id=s["service_id"])
                        BookingService.objects.create(booking=booking, service=service)
                        saved_services.append(service.child_service_name)

                booking.calculate_totals()

        except Exception as e:
            return Response({"detail": "Booking error", "error": str(e)}, status=500)

        #SEND NOTIFICATION TO ADMIN HERE
        create_admin_notification(booking)


        response = {
            "booking_id": booking.id,
            "username": request.user.username,
            "email": request.user.email,
            "date": str(start_slot.slot_date),
            "time": f"{start_slot.slot_master.start_time} - {start_slot.slot_master.end_time}",
            "services": saved_services,
            "total_price": float(booking.grand_total),
            "status": booking.status,
        }
        return Response(response, status=201)
    

class AdminNotificationListView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        notifications = AdminNotification.objects.filter(is_read=False).order_by("-created_at")

        return Response([
            {
                "id": n.id,
                "booking_id": n.booking.id,
                "message": n.message,
                "created_at": n.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                "status": n.booking.status,
            }
            for n in notifications
        ], status=200)


class AdminNotificationMarkReadView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, notif_id):
        notif = get_object_or_404(AdminNotification, id=notif_id)
        notif.is_read = True
        notif.read_by = request.user
        notif.save()
        return Response({"detail": "Notification cleared"}, status=200)



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

         # Mark related notification as handled
        AdminNotification.objects.filter(booking=booking).update(is_read=True, read_by=request.user)


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

        # Clear notification
        AdminNotification.objects.filter(booking=booking).update(is_read=True, read_by=request.user)


        return Response({"detail": "Booking declined and slots freed"}, status=200)


class BookingHistoryView(APIView):
    permission_classes = [permissions.IsAdminUser]  # 🔐 ADMIN ONLY

    def get(self, request):
        bookings = (
            Booking.objects
            .select_related("user", "start_slot__slot_master")
            .prefetch_related("services__service")
            .order_by("-created_at")
        )

        serializer = BookingSerializer(bookings, many=True)
        return Response(serializer.data, status=200)


def mark_completed_bookings():
    """
    Mark bookings as completed if slot end time is passed.
    """
    now = timezone.now()

    # Only check confirmed bookings
    bookings = (
        Booking.objects
        .filter(status="confirmed")
        .select_related("start_slot__slot_master")
    )

    for booking in bookings:
        slot = booking.start_slot
        slot_master = slot.slot_master

        # Combine slot date + end time
        slot_end_datetime = timezone.make_aware(
            datetime.combine(slot.slot_date, slot_master.end_time)
        )

        if now > slot_end_datetime:
            booking.status = "completed"
            booking.save(update_fields=["status"])


class AdminbookingStatsView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        # 🔥 IMPORTANT: auto-update completed bookings first
        mark_completed_bookings()

        total_orders = Booking.objects.count()
        completed_orders = Booking.objects.filter(status="completed").count()
        pending_orders = Booking.objects.filter(status="pending").count()

        return Response(
            {
                "total_orders": total_orders,
                "completed_orders": completed_orders,
                "pending_orders": pending_orders,
            },
            status=200
        )

class AdminSalesStatsView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        now = timezone.now()
        last_24_hours = now - timedelta(hours=24)

        completed_bookings = Booking.objects.filter(
            status="completed",
            created_at__gte=last_24_hours
        )

        # 1️⃣ SALES (count)
        sales_count = completed_bookings.count()

        # 2️⃣ REVENUE (Decimal)
        revenue = completed_bookings.aggregate(
            total=Sum("grand_total")
        )["total"] or Decimal("0.00")

        # 3️⃣ EXPENSES (20% of revenue)
        expenses = revenue * Decimal("0.20")

        return Response(
            {
                "sales": sales_count,
                "revenue": float(revenue),
                "expenses": float(expenses),
                "time_range": "last_24_hours"
            },
            status=200
        )

class AdminCustomerTrendView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        """
        Returns customer visit trend for last 6 months
        """

        today = timezone.now().date()
        six_months_ago = today - timedelta(days=180)

        # Group completed bookings by month
        qs = (
            Booking.objects
            .filter(
                status="completed",
                created_at__date__gte=six_months_ago
            )
            .annotate(month=TruncMonth("created_at"))
            .values("month")
            .annotate(visits=Count("id"))
            .order_by("month")
        )

        # Prepare response
        labels = []
        data = []

        for row in qs:
            labels.append(row["month"].strftime("%b"))  # Jan, Feb, Mar
            data.append(row["visits"])

        return Response(
            {
                "labels": labels,
                "data": data
            },
            status=200
        )








