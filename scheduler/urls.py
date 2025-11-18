from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    SlotMasterViewSet,
    HolidayViewSet,
    WorkingDayViewSet,
    DailySlotListAPIView
)

router = DefaultRouter()
router.register(r'slotmasters', SlotMasterViewSet, basename='slotmaster')
router.register(r'holidays', HolidayViewSet, basename='holiday')
router.register(r'workingdays', WorkingDayViewSet, basename='workingday')

urlpatterns = [
    path('', include(router.urls)),
    path('slots/', DailySlotListAPIView.as_view(), name='daily-slots'),
]
