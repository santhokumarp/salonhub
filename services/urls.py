from django.urls import path
from .views import (
    # admin
    AdminMainUnderGenderView,
    AdminMainServicesView,
    AdminChildServiceView,
    AdminChildServiceDetailView,
    # user
    UserGenderListView,
    UserMainServicesByGenderView,
    UserChildServicesView,
    UserSingleChildServiceView,
    # optional: GenderView (admin single/list) - if you still want
)

urlpatterns = [
    # ---------------- ADMIN main creation under a gender ----------------
    path('admin/gender/<int:gender_id>/main/', AdminMainUnderGenderView.as_view(), name='admin_main_create_under_gender'),

    # ---------------- ADMIN main CRUD ----------------
    path('admin/main/', AdminMainServicesView.as_view(), name='admin_main_list'),
    path('admin/main/<int:service_id>/', AdminMainServicesView.as_view(), name='admin_main_detail'),

    # ---------------- ADMIN child CRUD (scoped to main) ----------------
    path('admin/main/<int:main_service_id>/child/', AdminChildServiceView.as_view(), name='admin_child_list_create'),
    path('admin/main/<int:main_service_id>/child/<int:child_id>/', AdminChildServiceDetailView.as_view(), name='admin_child_detail'),

    # ---------------- USER public endpoints ----------------
    path('user/genders/', UserGenderListView.as_view(), name='user_genders'),
    path('user/main/', UserMainServicesByGenderView.as_view(), name='user_main_by_gender'),
    path('user/main/<int:main_service_id>/child/', UserChildServicesView.as_view(), name='user_child_services'),
    path('user/child/<int:child_id>/', UserSingleChildServiceView.as_view(), name='user_single_child'),
]

