from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions, parsers
from django.shortcuts import get_object_or_404
from .models import Gender, MainServices, Child_services
from .serializers import GenderSerializer, MainServicesSerializer, ChildServiceSerializer
from rest_framework.permissions import IsAuthenticated,AllowAny
from accounts.permissions import IsAdmin


class GenderView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, gender_id=None):
        # GET single gender
        if gender_id:
            gender = get_object_or_404(Gender, pk=gender_id)
            serializer = GenderSerializer(gender)
            return Response(serializer.data)

        # GET all genders
        genders = Gender.objects.all()
        serializer = GenderSerializer(genders, many=True)
        return Response(serializer.data)
    


class MainServicesView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, service_id=None):
        gender_id = request.query_params.get('gender_id')

        # 1️⃣ Fetch a single service if ID is given
        if service_id is not None:
            service = get_object_or_404(MainServices, pk=service_id)
            serializer = MainServicesSerializer(service)
            return Response(serializer.data, status=200)

        # 2️⃣ Filter based on gender_id
        if gender_id:
            services = MainServices.objects.filter(
                gender_id=gender_id
            ).select_related("gender")

            # Handle empty list properly
            if not services.exists():
                return Response(
                    {"message": "No main services found for this gender"},
                    status=status.HTTP_404_NOT_FOUND
                )

            serializer = MainServicesSerializer(services, many=True)
            return Response(serializer.data, status=200)

        # 3️⃣ Return all main services
        services = MainServices.objects.all().select_related("gender")
        serializer = MainServicesSerializer(services, many=True)
        return Response(serializer.data, status=200)

    

class AdminChildServiceView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsAdmin]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]

    def post(self, request, main_service_id):
        main_service = get_object_or_404(MainServices, pk=main_service_id)
        gender = main_service.gender

        child_service = Child_services.objects.create(
            main_services=main_service,
            gender=gender,
            child_service_name=request.data.get("child_service_name"),
            child_service_description=request.data.get("child_service_description"),
            price=request.data.get("price"),
            duration=request.data.get("duration", 30),
            image=request.data.get("image")
        )

        return Response({
            "message": "Child service created successfully",
            "data": ChildServiceSerializer(child_service, context={'request': request}).data
        }, status=201)

    def get(self, request, main_service_id):
        services = Child_services.objects.filter(main_services_id=main_service_id)
        serializer = ChildServiceSerializer(services, many=True, context={'request': request})
        return Response(serializer.data)

    #Single Child Service Edit/Delete

class AdminChildServiceDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsAdmin]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]

    def get(self, request, pk):
        service = get_object_or_404(Child_services, pk=pk)
        serializer = ChildServiceSerializer(service, context={'request': request})
        return Response(serializer.data)

    def put(self, request, pk):
        service = get_object_or_404(Child_services, pk=pk)
        serializer = ChildServiceSerializer(service, data=request.data, partial=False, context={'request': request})

        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Child Service updated successfully"})
        return Response(serializer.errors, status=400)

    def patch(self, request, pk):
        service = get_object_or_404(Child_services, pk=pk)
        serializer = ChildServiceSerializer(service, data=request.data, partial=True, context={'request': request})

        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Child Service partially updated"})
        return Response(serializer.errors, status=400)

    def delete(self, request, pk):
        service = get_object_or_404(Child_services, pk=pk)
        service.delete()
        return Response({"message": "Child Service deleted successfully"}, status=204)

    
class ChildServicesByMainServiceView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, main_service_id):
        child_services = Child_services.objects.filter(
            main_services_id=main_service_id
        ).select_related('gender', 'main_services')

        serializer = ChildServiceSerializer(child_services, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)





###################### USER VIEW ##################

# ===========================
# USER API — NO AUTH REQUIRED
# ===========================

class UserGenderListView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        genders = Gender.objects.all()
        serializer = GenderSerializer(genders, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class UserMainServicesByGenderView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        gender_id = request.query_params.get("gender_id")

        if not gender_id:
            return Response({"error": "gender_id is required"}, status=400)

        services = MainServices.objects.filter(gender_id=gender_id)

        if not services.exists():
            return Response({"message": "No main services found"}, status=404)

        serializer = MainServicesSerializer(services, many=True)
        return Response(serializer.data, status=200)




class UserChildServicesView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, main_service_id):
        services = Child_services.objects.filter(main_services_id=main_service_id)

        if not services.exists():
            return Response(
                {"message": "No child services found"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = ChildServiceSerializer(services, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)



class UserSingleChildServiceView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, child_id):
        service = get_object_or_404(Child_services, pk=child_id)
        serializer = ChildServiceSerializer(service, context={'request': request})
        return Response(serializer.data)

