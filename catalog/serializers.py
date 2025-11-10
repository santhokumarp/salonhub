from rest_framework import serializers
from .models import Category, SubCategory, Service

class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = fields = ['id', 'subcategory', 'name', 'description', 'price', 'image', 'created_at', 'updated_at']


class SubCategorySerializer(serializers.ModelSerializer):
    services = ServiceSerializer(many=True, read_only=True)

    class Meta:
        model = SubCategory
        fields = ['id', 'name', 'category', 'services']


class CategorySerializer(serializers.ModelSerializer):
    subcategories = SubCategorySerializer(many=True, read_only=True)

    class Meta:
        model = Category
        fields = ['id', 'name', 'subcategories']
        