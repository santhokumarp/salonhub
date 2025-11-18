from rest_framework import serializers
from .models import Booking, BookingService, CartItem
from services.models import Child_services
from scheduler.serializers import DailySlotSerializer


# ------------------------------
# CART ITEM SERIALIZER
# ------------------------------
class CartItemSerializer(serializers.ModelSerializer):
    service_name = serializers.CharField(source="service.child_service_name", read_only=True)
    price = serializers.CharField(source="service.price", read_only=True)

    class Meta:
        model = CartItem
        fields = ["id", "service", "service_name", "price", "quantity"]


# ------------------------------
# BOOKING SERVICE SERIALIZER
# ------------------------------
class BookingServiceSerializer(serializers.ModelSerializer):
    service_name = serializers.CharField(source="service.child_service_name")
    price = serializers.CharField(source="service.price")
    duration = serializers.IntegerField(source="service.duration")

    class Meta:
        model = BookingService
        fields = ["service", "service_name", "price", "duration"]


# ------------------------------
# BOOKING SERIALIZER
# ------------------------------
class BookingSerializer(serializers.ModelSerializer):
    services = BookingServiceSerializer(many=True)
    start_slot = DailySlotSerializer()
    user = serializers.StringRelatedField()

    class Meta:
        model = Booking
        fields = [
            "id", "user", "start_slot", "status", "created_at",
            "total_price", "gst_amount", "grand_total",
            "services"
        ]
