from rest_framework import viewsets, permissions, generics
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter

from .models import SlotMaster, WorkingDay, Holiday, DailySlot
from .serializers import (
    SlotMasterSerializer,
    WorkingDaySerializer,
    HolidaySerializer,
    DailySlotSerializer
)


class SlotMasterViewSet(viewsets.ModelViewSet):
    queryset = SlotMaster.objects.all().order_by("start_time")
    serializer_class = SlotMasterSerializer
    permission_classes = [permissions.IsAdminUser]


class WorkingDayViewSet(viewsets.ModelViewSet):
    queryset = WorkingDay.objects.all()
    serializer_class = WorkingDaySerializer
    permission_classes = [permissions.IsAdminUser]


class HolidayViewSet(viewsets.ModelViewSet):
    queryset = Holiday.objects.all()
    serializer_class = HolidaySerializer
    permission_classes = [permissions.IsAdminUser]


class DailySlotListAPIView(generics.ListAPIView):
    """
    USERS QUERY DAILY SLOTS HERE
    ?date=YYYY-MM-DD
    """
    serializer_class = DailySlotSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        date = self.request.query_params.get("date")
        if not date:
            return DailySlot.objects.none()

        return DailySlot.objects.filter(
            slot_date=date
        ).select_related("slot_master").order_by("slot_master__start_time")


