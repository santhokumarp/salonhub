from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .models import Category, SubCategory, Service
from .serializers import CategorySerializer, SubCategorySerializer, ServiceSerializer
from accounts.permissions import IsAdmin, IsUser
from rest_framework.parsers import JSONParser, FormParser, MultiPartParser


#  Admin Catalog View
class AdminCatalogView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsAdmin]
    parser_classes = [JSONParser, FormParser, MultiPartParser]

    # Admin can view all categories with subcategories and services
    def get(self, request):
        categories = Category.objects.prefetch_related('subcategories__services').all()
        serializer = CategorySerializer(categories, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # Admin can add new services dynamically (under an existing subcategory)
    def post(self, request):
        serializer = ServiceSerializer(data=request.data)
        if serializer.is_valid():
            service = serializer.save()
            response_data = ServiceSerializer(service).data
            return Response(
                {"message": "Service created successfully", "service": response_data},
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



#  User Catalog View

class UserCatalogView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsUser]

    # User can view all categories, subcategories, and services
    def get(self, request):
        categories = Category.objects.prefetch_related('subcategories__services').all()
        serializer = CategorySerializer(categories, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


# Admin Service Management (CRUD)

class AdminServiceView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsAdmin]

    # Admin can view all services
    def get(self, request):
        services = Service.objects.all().order_by('-created_at')
        serializer = ServiceSerializer(services, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # Admin can create a new service
    def post(self, request):
        serializer = ServiceSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Service created successfully", "service": serializer.data},
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # Admin can update a service
    def put(self, request, pk=None):
        if not pk:
            return Response({"error": "Service ID is required for update"}, status=status.HTTP_400_BAD_REQUEST)

        service = get_object_or_404(Service, id=pk)
        serializer = ServiceSerializer(service, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Service updated successfully", "service": serializer.data},
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # Admin can delete a service
    def delete(self, request, pk=None):
        if not pk:
            return Response({"error": "Service ID is required for delete"}, status=status.HTTP_400_BAD_REQUEST)

        service = get_object_or_404(Service, id=pk)
        service.delete()
        return Response({"message": "Service deleted successfully"}, status=status.HTTP_200_OK)



# User Service View (Read Only)

class UserServiceView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsUser]

    # Users can only view all available services
    def get(self, request):
        services = Service.objects.all().order_by('-created_at')
        serializer = ServiceSerializer(services, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

            
           


# 🔹 1. AdminCatalogView

# GET: Shows entire catalog tree
# → Category → Subcategory → Services

# POST: Add a new Service (requires subcategory ID)

# 🔹 2. UserCatalogView

# GET: Users can view same catalog but read-only

# 🔹 3. AdminServiceView

# GET: All services flat list

# POST: Create new service

# PUT /api/catalog/admin/services/<id>/: Update service

# DELETE /api/catalog/admin/services/<id>/: Delete service

# 🔹 4. UserServiceView

# GET: View only flat list of all services
