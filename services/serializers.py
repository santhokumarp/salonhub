from rest_framework import serializers
from .models import Gender, MainServices, Child_services

class GenderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Gender
        fields = ['id', 'name']


class MainServicesSerializer(serializers.ModelSerializer):

    gender_id = serializers.PrimaryKeyRelatedField(
        queryset=Gender.objects.all(),
        source='gender',
        write_only=True
    )
    gender = serializers.CharField(source='gender.name', read_only=True)

    class Meta:
        model = MainServices
        fields = [
            'id',
            'main_services_name',
            'main_services_description',
            'gender_id',
            'gender'
        ]



#child serializers
class ChildServiceSerializer(serializers.ModelSerializer):
    gender_id = serializers.PrimaryKeyRelatedField(
        queryset=Gender.objects.all(),
        source='gender',
        write_only=True,
        required=False
    )

    main_service_id = serializers.PrimaryKeyRelatedField(
        queryset=MainServices.objects.all(),
        source='main_services',
        write_only=True
    )

    gender = serializers.CharField(source='gender.name', read_only=True)
    main_service = serializers.CharField(source='main_services.main_services_name', read_only=True)

    image = serializers.SerializerMethodField()

    class Meta:
        model = Child_services
        fields = [
            'id', 'child_service_name', 'child_service_description',
            'price', 'duration', 'image',
            'gender', 'gender_id',
            'main_service', 'main_service_id'
        ]

    def get_image(self, obj):
        request = self.context.get('request')
        return request.build_absolute_uri(obj.image.url) if obj.image else None

    

    


