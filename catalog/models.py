from django.db import models

#  Gender Table
class Gender(models.Model):
    GENDER_CHOICES = (
        ('male', 'Male'),
        ('female', 'Female'),
    )
    name = models.CharField(max_length=10, choices=GENDER_CHOICES, unique=True)

    def __str__(self):
        return self.name


#  SubCategory Table
class SubCategory(models.Model):
    gender = models.ForeignKey(Gender, on_delete=models.CASCADE, related_name='subcategories')
    name = models.CharField(max_length=100)

    class Meta:
        unique_together = ('gender', 'name')

    def __str__(self):
        return f"{self.name} ({self.gender.name})"


#  Service Table
class Service(models.Model):
    gender = models.ForeignKey(Gender, on_delete=models.CASCADE, null=True, blank=True, default=1)
    subcategory = models.ForeignKey(SubCategory, on_delete=models.CASCADE, related_name='services')
    name = models.CharField(max_length=100,default="Default Service")
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    image = models.ImageField(upload_to='services/', blank=True, null=True)
    duration = models.PositiveIntegerField(default=30)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.subcategory.name} - {self.gender.name})"



# Each subcategory belongs to a category (male/female).

# Each subcategory can have multiple services.

# Each service belongs to a subcategory.