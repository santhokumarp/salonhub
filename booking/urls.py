from django.urls import path
from .views import (
    CartAddView,
    CartView,
    CheckoutView,
    AdminAcceptView,
    AdminDeclineView,
    BookingHistoryView,
    AdminNotificationListView,
    AdminNotificationMarkReadView,
    AdminbookingStatsView,
    AdminSalesStatsView,
    AdminCustomerTrendView
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
    path("admin/notifications/", AdminNotificationListView.as_view(), name="admin-notifications"),
    path("admin/notifications/<int:notif_id>/read/", AdminNotificationMarkReadView.as_view()),
    path('admin/accept/', AdminAcceptView.as_view(), name='booking-admin-accept'),
    path('admin/decline/', AdminDeclineView.as_view(), name='booking-admin-decline'),
    path("admin/orders/stats/", AdminbookingStatsView.as_view()),
     path("admin/sales/stats/", AdminSalesStatsView.as_view()),
     path("admin/customers/trend/", AdminCustomerTrendView.as_view()),
]

