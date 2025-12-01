from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User, Role
from django.db.models import Q



class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role', 'phone']



# Register Serializer with Confirm Password Validation
class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)
    confirm_password = serializers.CharField(write_only=True, required=True)
    # role = serializers.CharField(write_only=True, required=False)
    

    class Meta:
        model = User
        fields = ['username', 'email', 'phone', 'password', 'confirm_password']
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def validate(self, data):
         # Check password match
         if data['password'] != data['confirm_password']:
             raise serializers.ValidationError({"password": "Passwords do not match."})
         return data
    
    def create(self, validated_data):
         # Remove confirm_password before creating user
        validated_data.pop('confirm_password', None)
        password = validated_data.pop('password', None)
        role_name = self.context.get('role_name', 'user')
        role_obj, _ = Role.objects.get_or_create(name=role_name)
        user = User.objects.create_user(**validated_data, password=password, role=role_obj)
        return user



class LoginSerializer(serializers.Serializer):
    email_or_username = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        email_or_username = data.get('email_or_username')
        password = data.get('password')

        user = None

        # ✅ Login with email
        if '@' in email_or_username:
            try:
                user_obj = User.objects.get(email=email_or_username)
                user = authenticate(email=user_obj.email, password=password)
            except User.DoesNotExist:
                raise serializers.ValidationError("Invalid email or password.")
        else:
            # ✅ Login with username
            try:
                user_obj = User.objects.get(username=email_or_username)
                user = authenticate(email=user_obj.email, password=password)
            except User.DoesNotExist:
                raise serializers.ValidationError("Invalid username or password.")

        if not user:
            raise serializers.ValidationError("Invalid credentials.")

        if not user.is_active:
            raise serializers.ValidationError("Account is inactive.")

        # ✅ Return actual user instance
        return user

    

    

