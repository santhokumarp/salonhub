from django.urls import path
from .views import (
    CartAddView,
    CartView,
    CheckoutView,
    AdminAcceptView,
    AdminDeclineView,
    BookingHistoryView
)

urlpatterns = [
    path('cart/add/', CartAddView.as_view(), name='cart-add'),
    path('cart/', CartView.as_view(), name='cart-view'),

    path('checkout/', CheckoutView.as_view(), name='checkout'),

    path('admin/accept/', AdminAcceptView.as_view(), name='admin-accept'),
    path('admin/decline/', AdminDeclineView.as_view(), name='admin-decline'),

    path('history/', BookingHistoryView.as_view(), name='booking-history'),
]
