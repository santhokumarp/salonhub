from rest_framework import serializers
from .models import Gender, MainServices, Child_services

# -------------------------
# Gender (simple)
# -------------------------
class GenderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Gender
        fields = ['id', 'name']


# -------------------------
# MainServices Serializer
# - gender is read-only for responses (we set gender in view)
# -------------------------
class MainServicesSerializer(serializers.ModelSerializer):
    gender = serializers.CharField(source='gender.name', read_only=True)
    # include gender id in response for convenience
    gender_id = serializers.IntegerField(source='gender.id', read_only=True)

    class Meta:
        model = MainServices
        fields = ['id', 'main_services_name', 'main_services_description', 'gender', 'gender_id']


# -------------------------
# Child Service Serializer
# - main_service is read-only in response (we set from view)
# - image is returned as absolute URL when available
# -------------------------
class ChildServiceSerializer(serializers.ModelSerializer):
    main_service = serializers.IntegerField(source='main_services.id', read_only=True)
    main_service_name = serializers.CharField(source='main_services.main_services_name', read_only=True)
    gender = serializers.CharField(source='gender.name', read_only=True)
    image = serializers.SerializerMethodField()

    class Meta:
        model = Child_services
        fields = [
            'id',
            'child_service_name',
            'child_service_description',
            'price',
            'duration',
            'image',
            'main_service',
            'main_service_name',
            'gender',
        ]

    def get_image(self, obj):
        request = self.context.get('request')
        if obj.image:
            return request.build_absolute_uri(obj.image.url)
        return None

    def validate_price(self, value):
        if value is None:
            raise serializers.ValidationError("Price is required.")
        try:
            if float(value) <= 0:
                raise serializers.ValidationError("Price must be greater than 0.")
        except Exception:
            raise serializers.ValidationError("Price must be a valid number.")
        return value




