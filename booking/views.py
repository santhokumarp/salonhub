from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from datetime import timedelta

from .models import CartItem, Booking, BookingService, RESERVATION_MINUTES
from .serializers import CartItemSerializer, BookingSerializer
from scheduler.models import DailySlot, SlotMaster
from services.models import Child_services
from booking.helpers import compute_required_slot_master_ids



class CartAddView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        if request.user.is_anonymous:
            return Response({"error": "Authentication required"}, status=401)

        service_id = request.data.get("service_id")
        service = get_object_or_404(Child_services, id=service_id)

        item, created = CartItem.objects.get_or_create(
            user=request.user,
            service=service
        )

        if not created:
            item.quantity += 1
            item.save()

        return Response({"detail": "Service added to cart"}, status=201)


class CartView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if request.user.is_anonymous:
            return Response({"error": "Authentication required"}, status=401)

        items = CartItem.objects.filter(user=request.user)
        ser = CartItemSerializer(items, many=True)

        subtotal = sum([float(i.service.price) * i.quantity for i in items])
        gst = subtotal * 0.18
        grand_total = subtotal + gst

        return Response({
            "items": ser.data,
            "subtotal": subtotal,
            "gst": gst,
            "grand_total": grand_total
        })


class CheckoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        start_slot_id = request.data.get("start_slot_id")
        start_slot = get_object_or_404(DailySlot, id=start_slot_id)

        cart_items = CartItem.objects.filter(user=request.user)
        if not cart_items.exists():
            return Response({"detail": "Cart empty"}, status=400)

        # Total duration needed
        total_minutes = sum([ci.service.duration for ci in cart_items])

        with transaction.atomic():
            start_slot = DailySlot.objects.select_for_update().get(id=start_slot_id)

            if start_slot.status != "available":
                return Response({"detail": "Selected slot not available"}, status=400)

            slot_masters = SlotMaster.objects.filter(is_active=True).order_by("start_time")
            needed = compute_required_slot_master_ids(
                start_slot.slot_master, slot_masters, total_minutes
            )

            if not needed:
                return Response({"detail": "Not enough consecutive slots"}, status=400)

            required_slots = list(
                DailySlot.objects.select_for_update().filter(
                    slot_master_id__in=needed,
                    slot_date=start_slot.slot_date
                )
            )

            for ds in required_slots:
                if ds.status != "available":
                    return Response({"detail": "Some slots are already booked"}, status=400)

            # Reserve slots
            reserved_until = timezone.now() + timedelta(minutes=RESERVATION_MINUTES)
            for ds in required_slots:
                ds.status = "reserved"
                ds.reserved_by = request.user
                ds.reserved_until = reserved_until
                ds.save()

            # Create pending booking
            booking = Booking.objects.create(
                user=request.user,
                start_slot=start_slot,
                status="pending",
            )

            # Add booking services
            for ci in cart_items:
                BookingService.objects.create(booking=booking, service=ci.service)

            booking.calculate_totals()

            # Clear cart
            cart_items.delete()

        return Response({
            "detail": "Booking pending admin approval",
            "booking_id": booking.id
        }, status=201)


# ADMIN APIViews


class AdminAcceptView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request):
        booking_id = request.data.get("booking_id")
        booking = get_object_or_404(Booking, id=booking_id)

        booking.status = "confirmed"
        booking.save()

        start = booking.start_slot
        total_minutes = sum([bs.service.duration for bs in booking.services.all()])
        slot_masters = SlotMaster.objects.filter(is_active=True).order_by("start_time")

        needed = compute_required_slot_master_ids(start.slot_master, slot_masters, total_minutes)

        reserved_slots = DailySlot.objects.filter(
            slot_master_id__in=needed,
            slot_date=start.slot_date
        )

        for ds in reserved_slots:
            ds.status = "booked"
            ds.booked_by = booking.user
            ds.booked_service = booking.services.first().service
            ds.reserved_by = None
            ds.reserved_until = None
            ds.save()

        return Response({"detail": "Booking confirmed"})




class AdminDeclineView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request):
        booking_id = request.data.get("booking_id")
        booking = get_object_or_404(Booking, id=booking_id)

        booking.status = "declined"
        booking.save()

        start = booking.start_slot
        total_minutes = sum([bs.service.duration for bs in booking.services.all()])
        slot_masters = SlotMaster.objects.filter(is_active=True).order_by("start_time")

        needed = compute_required_slot_master_ids(start.slot_master, slot_masters, total_minutes)

        DailySlot.objects.filter(
            slot_master_id__in=needed,
            slot_date=start.slot_date
        ).update(
            status="available",
            reserved_by=None,
            reserved_until=None
        )

        return Response({"detail": "Booking declined"})


class BookingHistoryView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        bookings = Booking.objects.filter(user=request.user)
        ser = BookingSerializer(bookings, many=True)
        return Response(ser.data)



