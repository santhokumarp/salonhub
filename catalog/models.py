from django.db import models



#Male / Female main category
class Category(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name
    
# Example: Hair, Facial, Beard, etc.
class SubCategory(models.Model):

    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='subcategories')
    name = models.CharField(max_length=100)

    class Meta:
        unique_together = ('category', 'name')

        def __str__(self):
            return f"{self.name} ({self.category.name})"

# Individual services under a subcategory
#Example: Haircut, Hair Wash, Hair Coloring
class Service(models.Model):
    # CATEGORY_CHOICES = (
    #     ('male', 'Male'),
    #     ('female', 'Female'),)
    
    subcategory = models.ForeignKey(SubCategory, on_delete=models.CASCADE, related_name='services'),
    name = models.CharField(max_length=100),
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    image = models.ImageField(upload_to='services/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.subcategory.name})"


# Each subcategory belongs to a category (male/female).

# Each subcategory can have multiple services.

# Each service belongs to a subcategory.