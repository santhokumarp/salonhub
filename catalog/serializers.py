from rest_framework import serializers
from .models import Gender, SubCategory, Service


# ✅ GENDER SERIALIZER
class GenderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Gender
        fields = ['id', 'name']


# ✅ SUBCATEGORY SERIALIZER
class SubCategorySerializer(serializers.ModelSerializer):
    gender = GenderSerializer(read_only=True)
    gender_id = serializers.PrimaryKeyRelatedField(
        queryset=Gender.objects.all(),
        source='gender',
        write_only=True
    )

    class Meta:
        model = SubCategory
        fields = ['id', 'name', 'description', 'gender', 'gender_id']


# ✅ SERVICE SERIALIZER (for user view)
class ServiceSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = Service
        fields = ['id', 'name', 'description', 'price', 'duration', 'image']

    def get_image(self, obj):
        request = self.context.get('request')
        return request.build_absolute_uri(obj.image.url) if obj.image else None


# ✅ SUBCATEGORY TREE SERIALIZER (nested for user)
class SubCategoryTreeSerializer(serializers.ModelSerializer):
    services = ServiceSerializer(many=True, read_only=True)

    class Meta:
        model = SubCategory
        fields = ['id', 'name', 'description', 'services']


# ✅ GENDER TREE SERIALIZER (nested for user)
class GenderTreeSerializer(serializers.ModelSerializer):
    subcategories = SubCategoryTreeSerializer(many=True, read_only=True)

    class Meta:
        model = Gender
        fields = ['id', 'name', 'subcategories']


# ✅ ADMIN CRUD SERVICE SERIALIZER
class CRUDServiceSerializer(serializers.ModelSerializer):
    gender = serializers.CharField(write_only=True, required=False)
    subcategory = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = Service
        fields = ['id', 'gender', 'subcategory', 'name', 'description', 'price', 'duration', 'image']

    def validate(self, attrs):
        gender_value = attrs.get('gender')
        subcategory_value = attrs.get('subcategory')

        # Handle gender by name or id automatically
        if isinstance(gender_value, str):
            gender_obj = Gender.objects.filter(name__iexact=gender_value.strip()).first()
            if not gender_obj:
                raise serializers.ValidationError({"gender": f"Gender '{gender_value}' not found."})
            attrs['gender'] = gender_obj

        elif isinstance(gender_value, int):
            gender_obj = Gender.objects.filter(pk=gender_value).first()
            if not gender_obj:
                raise serializers.ValidationError({"gender": f"Gender id '{gender_value}' not found."})
            attrs['gender'] = gender_obj

        # Handle subcategory by name or id automatically
        if isinstance(subcategory_value, str):
            subcat_obj = SubCategory.objects.filter(name__iexact=subcategory_value.strip()).first()
            if not subcat_obj:
                raise serializers.ValidationError({"subcategory": f"SubCategory '{subcategory_value}' not found."})
            attrs['subcategory'] = subcat_obj

        elif isinstance(subcategory_value, int):
            subcat_obj = SubCategory.objects.filter(pk=subcategory_value).first()
            if not subcat_obj:
                raise serializers.ValidationError({"subcategory": f"SubCategory id '{subcategory_value}' not found."})
            attrs['subcategory'] = subcat_obj

        return attrs

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        request = self.context.get('request')
        rep['gender'] = instance.gender.name
        rep['subcategory'] = instance.subcategory.name
        rep['image'] = request.build_absolute_uri(instance.image.url) if instance.image else None
        return rep


# ✅ ONE-CLICK CREATION SERIALIZER (Gender → SubCategory → Service)
class CreateAllSerializer(serializers.Serializer):
    gender_name = serializers.ChoiceField(choices=[('male', 'Male'), ('female', 'Female')])
    subcategory_name = serializers.CharField(max_length=100)
    subcategory_description = serializers.CharField(required=False, allow_blank=True)
    service_name = serializers.CharField(max_length=100)
    description = serializers.CharField(required=False, allow_blank=True)
    price = serializers.DecimalField(max_digits=8, decimal_places=2)
    duration = serializers.IntegerField(default=30)
    image = serializers.ImageField(required=False, allow_null=True)

    def create(self, validated_data):
        gender_name = validated_data.get('gender_name').lower().strip()
        subcategory_name = validated_data.get('subcategory_name').strip()
        subcategory_description = validated_data.get('subcategory_description', '').strip()
        service_name = validated_data.get('service_name').strip()

        # 1️⃣ Get or create gender
        gender, _ = Gender.objects.get_or_create(name=gender_name)

        # 2️⃣ Get or create subcategory with description
        subcategory, created = SubCategory.objects.get_or_create(
            gender=gender,
            name=subcategory_name,
            defaults={'description': subcategory_description}
        )

        # If subcategory existed but description changed, update it
        if not created and subcategory_description and subcategory.description != subcategory_description:
            subcategory.description = subcategory_description
            subcategory.save()

        # 3️⃣ Create the service linked to gender & subcategory
        service = Service.objects.create(
            gender=gender,
            subcategory=subcategory,
            name=service_name,
            description=validated_data.get('description', ''),
            price=validated_data.get('price'),
            duration=validated_data.get('duration', 30),
            image=validated_data.get('image', None)
        )
        return service



        
        