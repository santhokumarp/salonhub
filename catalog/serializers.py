from rest_framework import serializers
from .models import Gender, SubCategory, Service


class GenderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Gender
        fields = ['id', 'name']


class SubCategorySerializer(serializers.ModelSerializer):
    gender = GenderSerializer(read_only=True)

    class Meta:
        model = SubCategory
        fields = ['id', 'name', 'gender']


class ServiceSerializer(serializers.ModelSerializer):
    gender = GenderSerializer(read_only=True)
    subcategory = SubCategorySerializer(read_only=True)

    class Meta:
        model = Service
        fields = ['id', 'name', 'description', 'price', 'image', 'duration', 'subcategory', 'gender']


#  Single API Serializer for Create
class CreateAllSerializer(serializers.Serializer):
    gender_name = serializers.ChoiceField(choices=[('male', 'Male'), ('female', 'Female')])
    subcategory_name = serializers.CharField(max_length=100)
    service_name = serializers.CharField(max_length=100)
    description = serializers.CharField(required=False, allow_blank=True)
    price = serializers.DecimalField(max_digits=8, decimal_places=2)
    duration = serializers.IntegerField(required=False, default=30)
    image = serializers.ImageField(required=False)

    def create(self, validated_data):
        gender_name = validated_data.get('gender_name')
        subcategory_name = validated_data.get('subcategory_name')

        #  Get or create Gender
        gender, _ = Gender.objects.get_or_create(name=gender_name)

        #  Get or create SubCategory
        subcategory, _ = SubCategory.objects.get_or_create(
            gender=gender,
            name=subcategory_name
        )

        # Create Service
        service = Service.objects.create(
            gender=gender,
            subcategory=subcategory,
            name=validated_data.get('service_name'),
            description=validated_data.get('description', ''),
            price=validated_data.get('price'),
            image=validated_data.get('image', None),
            duration=validated_data.get('duration', 30)
        )
        return service


        
        