from django.urls import path
from .views import (
    GenderView, MainServicesView,
    AdminChildServiceView, AdminChildServiceDetailView,
    ChildServicesByMainServiceView,
    UserGenderListView, UserMainServicesByGenderView,
    UserChildServicesView, UserSingleChildServiceView
)

urlpatterns = [

    # ADMIN
    path('gender/', GenderView.as_view(), name='gender_list'),
    path('gender/<int:gender_id>/', GenderView.as_view(), name='gender_detail'),

    path('main_service/', MainServicesView.as_view(), name='main_service_list'),
    path('main_service/<int:service_id>/', MainServicesView.as_view(), name='main_service_detail'),

    # ADMIN Child
    path('admin/child/<int:main_service_id>/', AdminChildServiceView.as_view(), name='admin_child_create'),
    path('admin/child/detail/<int:pk>/', AdminChildServiceDetailView.as_view(), name='admin_child_detail'),

    # PUBLIC — child services under main service
    path('main/<int:main_service_id>/child/', ChildServicesByMainServiceView.as_view(), name='child_by_main'),

    # USER APIs
    path('user/genders/', UserGenderListView.as_view(), name='user_genders'),
    path('user/main/', UserMainServicesByGenderView.as_view(), name='user_main_services'),
    path('user/main/<int:main_service_id>/child/', UserChildServicesView.as_view(), name='user_child_services'),
    path('user/child/<int:child_id>/', UserSingleChildServiceView.as_view(), name='user_single_child'),
]
