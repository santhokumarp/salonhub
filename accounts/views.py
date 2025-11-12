from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate

from .models import User
from .serializers import RegisterSerializer, LoginSerializer, UserSerializer
from .permissions import IsAdmin, IsUser


# Helper function to create JWT tokens
def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        }



#USER REGISTRATION & LOGIN

class UserRegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        
        # data['role'] = 'user'
        serializer = RegisterSerializer(data=request.data, context={'role_name': 'user'})
        if serializer.is_valid():
            serializer.save()
            return Response(
                 {"message": "User registered successfully"},
                 status=status.HTTP_201_CREATED
                 )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data
            tokens = get_tokens_for_user(user)
            return Response({
                "message": "Login successful",
                "tokens": tokens,
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "role": user.role.name
                }
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


#ADMIN REGISTRATION & LOGIN
class AdminRegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        # data['role'] = 'admin'    
        serializer = RegisterSerializer(data=request.data, context={'role_name': 'admin'})
        if serializer.is_valid():
            user = serializer.save()
            user.is_staff = True 
            user.save()
            return Response(
                {"message": "Admin registered successfully"},
                status=status.HTTP_201_CREATED
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)
    



