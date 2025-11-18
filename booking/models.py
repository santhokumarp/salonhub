from django.db import models
from django.conf import settings
from scheduler.models import DailySlot
from services.models import Child_services
from django.utils import timezone
from datetime import timedelta


# Slot reservation duration before admin approval
RESERVATION_MINUTES = 15   # slot auto free after 15min if admin not approved


# ------------------------------
# 1) CART ITEM
# ------------------------------
class CartItem(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="cart_items"
    )
    service = models.ForeignKey(
        Child_services,
        on_delete=models.CASCADE
    )
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ('user', 'service')

    def __str__(self):
        return f"{self.user.username} → {self.service.child_service_name}"


# ------------------------------
# 2) BOOKING
# ------------------------------
class Booking(models.Model):

    STATUS_CHOICES = (
        ("pending", "Pending"),         # User submitted, admin must approve
        ("confirmed", "Confirmed"),     # Admin accepted
        ("declined", "Declined"),       # Admin rejected
        ("cancelled", "Cancelled"),
        ("completed", "Completed"),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='bookings'
    )

    start_slot = models.ForeignKey(
        DailySlot,
        on_delete=models.CASCADE,
        related_name="booking_start_slot"
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    # Billing
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    gst_percent = models.DecimalField(max_digits=5, decimal_places=2, default=18)
    gst_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    grand_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def calculate_totals(self):
        base = sum([item.service.price for item in self.services.all()])
        gst = (base * (self.gst_percent / 100))
        self.total_price = base
        self.gst_amount = gst
        self.grand_total = base + gst
        self.save(update_fields=['total_price', 'gst_amount', 'grand_total'])

    def __str__(self):
        return f"Booking #{self.id} - {self.user.username} ({self.status})"


# ------------------------------
# 3) SELECTED SERVICES INSIDE BOOKING
# ------------------------------
class BookingService(models.Model):
    booking = models.ForeignKey(
        Booking,
        on_delete=models.CASCADE,
        related_name='services'
    )
    service = models.ForeignKey(
        Child_services,
        on_delete=models.PROTECT
    )

    def __str__(self):
        return f"{self.booking.id} → {self.service.child_service_name}"

