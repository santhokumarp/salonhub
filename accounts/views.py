from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import status

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
        email_or_username = request.data.get("email_or_username")
        password = request.data.get("password")

        if not email_or_username or not password:
            return Response({"error": "email_or_username and password required"}, status=400)

        # Try email
        try:
            user = User.objects.get(email=email_or_username)
        except User.DoesNotExist:
            # Try username
            try:
                user = User.objects.get(username=email_or_username)
            except User.DoesNotExist:
                return Response({"error": "Invalid username/email or password"}, status=400)

        if not user.check_password(password):
            return Response({"error": "Invalid username/email or password"}, status=400)

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        access = refresh.access_token

        return Response({
            "access": str(access),
            "refresh": str(refresh),
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "phone": user.phone,
                 "role": user.role.name,
            }
        })




class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        refresh = request.data.get("refresh")

        if not refresh:
            return Response({"detail": "Refresh token required"}, status=400)

        try:
            token = RefreshToken(refresh)
            token.blacklist()
        except Exception:
            return Response({"detail": "Invalid or expired refresh token"}, status=400)

        return Response({"detail": "Logout successful"})





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
    



