from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions, parsers
from django.shortcuts import get_object_or_404
from django.core.cache import cache
from accounts.permissions import IsAdmin
from .models import Gender, SubCategory, Service
from .serializers import (
    GenderSerializer,
    SubCategorySerializer,
    CRUDServiceSerializer,
    GenderTreeSerializer,
    CreateAllSerializer
)


# -------------------- USER TREE (DSA Optimized) --------------------
class UserCatalogTreeView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        cached_data = cache.get('catalog_tree')
        if cached_data:
            return Response(cached_data)

        genders = Gender.objects.prefetch_related('subcategories__services').all()
        serializer = GenderTreeSerializer(genders, many=True, context={'request': request})
        cache.set('catalog_tree', serializer.data, 3600)
        return Response(serializer.data)


# -------------------- ADMIN: GENDER CRUD --------------------
class AdminGenderView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsAdmin]

    def post(self, request):
        serializer = GenderSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Gender created successfully"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk):
        gender = get_object_or_404(Gender, pk=pk)
        serializer = GenderSerializer(gender, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Gender updated successfully"}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        gender = get_object_or_404(Gender, pk=pk)
        gender.delete()
        return Response({"message": "Gender deleted successfully"}, status=status.HTTP_204_NO_CONTENT)


# -------------------- ADMIN: SUBCATEGORY CRUD --------------------
class AdminSubCategoryView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsAdmin]

    def post(self, request):
        serializer = SubCategorySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "SubCategory created successfully"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk):
        subcat = get_object_or_404(SubCategory, pk=pk)
        serializer = SubCategorySerializer(subcat, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "SubCategory updated successfully"}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        subcat = get_object_or_404(SubCategory, pk=pk)
        subcat.delete()
        return Response({"message": "SubCategory deleted successfully"}, status=status.HTTP_204_NO_CONTENT)


# -------------------- ADMIN: SERVICE CRUD --------------------
class AdminServiceView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsAdmin]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]

    def get(self, request):
        """
        Fetch all services (with gender and subcategory info)
        """
        cached_data = cache.get('all_services')
        if cached_data:
            return Response(cached_data, status=status.HTTP_200_OK)

        services = Service.objects.select_related('gender', 'subcategory').all()
        serializer = CRUDServiceSerializer(services, many=True, context={'request': request})
        cache.set('all_services', serializer.data, 3600)  # cache for 1 hour
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = CRUDServiceSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            service = serializer.save()
            cache.delete('catalog_tree')
            return Response({
                "message": "Service created successfully",
                "service": CRUDServiceSerializer(service, context={'request': request}).data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk):
        service = get_object_or_404(Service, pk=pk)
        serializer = CRUDServiceSerializer(service, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            cache.delete('catalog_tree')
            return Response({"message": "Service updated successfully"}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        service = get_object_or_404(Service, pk=pk)
        service.delete()
        cache.delete('catalog_tree')
        return Response({"message": "Service deleted successfully"}, status=status.HTTP_204_NO_CONTENT)


# -------------------- ADMIN: ONE-CLICK CREATION (Gender → SubCat → Service) --------------------
class AdminCreateAllView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsAdmin]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]

    def post(self, request):
        serializer = CreateAllSerializer(data=request.data)
        if serializer.is_valid():
            service = serializer.save()
            cache.delete('catalog_tree')
            return Response({
                "message": "Gender, SubCategory, and Service created successfully",
                "service_id": service.id,
                "service_name": service.name
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# -------------------- ADMIN: SERVICE DETAIL + EDIT --------------------
class AdminServiceDetailView(APIView):
    """
    Fetch or update a single service's full details (with gender/subcategory info).
    """
    permission_classes = [permissions.IsAuthenticated, IsAdmin]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]

    def get(self, request, pk):
        """Return all service details for editing"""
        service = get_object_or_404(Service, pk=pk)
        serializer = CRUDServiceSerializer(service, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        """Update all service fields"""
        service = get_object_or_404(Service, pk=pk)
        serializer = CRUDServiceSerializer(service, data=request.data, partial=False, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            cache.delete('catalog_tree')
            return Response({
                "message": "Service updated successfully",
                "service": serializer.data
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        """Allow partial update (like just name or price)"""
        service = get_object_or_404(Service, pk=pk)
        serializer = CRUDServiceSerializer(service, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            cache.delete('catalog_tree')
            return Response({
                "message": "Service partially updated successfully",
                "service": serializer.data
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



