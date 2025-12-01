from django.urls import path
from .views import (
    CartAddView,
    CartView,
    CheckoutView,
    AdminAcceptView,
    AdminDeclineView,
    BookingHistoryView,
)

urlpatterns = [

    # ------------------------------
    # CART ROUTES
    # ------------------------------
    path('cart/add/<int:service_id>/', CartAddView.as_view(), name='cart-add'),
    path('cart/', CartView.as_view(), name='cart-view'),

    # ------------------------------
    # USER BOOKING ROUTES
    # ------------------------------
    path('checkout/', CheckoutView.as_view(), name='booking-checkout'),
    path('history/', BookingHistoryView.as_view(), name='booking-history'),

    # ------------------------------
    # ADMIN BOOKING MANAGEMENT
    # ------------------------------
    path('admin/accept/', AdminAcceptView.as_view(), name='booking-admin-accept'),
    path('admin/decline/', AdminDeclineView.as_view(), name='booking-admin-decline'),
]

