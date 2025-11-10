from django.urls import path
from .views import AdminCreateAllView, UserCatalogView


urlpatterns = [
        # User
    path('user/service', UserCatalogView.as_view(), name='user_catalog'),

    path('admin/service/create/', AdminCreateAllView.as_view(), name='admin_create_all'),
    
]
