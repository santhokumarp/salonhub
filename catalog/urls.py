from django.urls import path
from .views import AdminCatalogView, UserCatalogView

urlpatterns = [
    path('admin/', AdminCatalogView.as_view(), name='admin_catalog'),
    path('user/', UserCatalogView.as_view(), name='user_catalog'),
]
