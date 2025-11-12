from django.urls import path
from .views import (
    AdminServiceView,
    AdminServiceDetailView,
    AdminGenderView,
    AdminSubCategoryView,
    AdminCreateAllView,
    UserCatalogTreeView
)

urlpatterns = [
    # USER TREE
    path('user/tree/', UserCatalogTreeView.as_view(), name='user_catalog_tree'),

    # ADMIN CRUD
    path('admin/service/', AdminServiceView.as_view(), name='admin_service_create'),
    path('admin/service/<int:pk>/', AdminServiceDetailView.as_view(), name='admin_service_detail'),  # ✅ NEW
    path('admin/service/<int:pk>/delete/', AdminServiceView.as_view(), name='admin_service_delete'),

    # ADMIN CREATE-ALL
    path('admin/createall/', AdminCreateAllView.as_view(), name='admin_create_all'),
 
    # GENDER & SUBCATEGORY
    path('admin/gender/', AdminGenderView.as_view(), name='admin_gender_create'),
    path('admin/subcategory/', AdminSubCategoryView.as_view(), name='admin_subcategory_create'),
]

