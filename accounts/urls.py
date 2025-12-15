from django.urls import path
from .views import (
    UserRegisterView, LoginView,
     AdminRegisterView,
     LogoutView,
    ProfileView,
    AdminCustomersDashboardView,
)

urlpatterns = [
    # User APIs
    path('register/', UserRegisterView.as_view(), name='user_register'),
    path('login/', LoginView.as_view(), name='user_login'),
    path('logout/', LogoutView.as_view(), name='logout'),

    # Admin APIs
    path('admin/register/', AdminRegisterView.as_view(), name='admin_register'),
    # path('admin/login/', LoginView.as_view(), name='admin_login'),

    # Common
    path('profile/', ProfileView.as_view(), name='profile'),
     path("admin/customers/dashboard/", AdminCustomersDashboardView.as_view()),
]