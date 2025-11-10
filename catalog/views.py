from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .models import Gender
from .serializers import CreateAllSerializer, GenderSerializer
from accounts.permissions import IsAdmin


# 👨‍💼 Admin: Create Gender + SubCategory + Service in one shot
class AdminCreateAllView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsAdmin]

    def post(self, request):
        serializer = CreateAllSerializer(data=request.data)
        if serializer.is_valid():
            service = serializer.save()
            return Response({
                "message": "Service, Subcategory, and Gender saved successfully!",
                "service": {
                    "id": service.id,
                    "name": service.name,
                    "subcategory": service.subcategory.name,
                    "gender": service.gender.name
                }
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# 🧍‍♂️ User: View all Genders, Subcategories, Services
class UserCatalogView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        genders = Gender.objects.prefetch_related('subcategories__services').all()
        result = []

        for gender in genders:
            gender_data = {
                "id": gender.id,
                "name": gender.name,
                "subcategories": []
            }
            for subcat in gender.subcategories.all():
                gender_data["subcategories"].append({
                    "id": subcat.id,
                    "name": subcat.name,
                    "services": [
                        {
                            "id": srv.id,
                            "name": srv.name,
                            "price": srv.price,
                            "description": srv.description,
                            "duration": srv.duration
                        }
                        for srv in subcat.services.all()
                    ]
                })
            result.append(gender_data)

        return Response(result, status=status.HTTP_200_OK)

