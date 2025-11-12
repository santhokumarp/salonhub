from django.db import models
from django.contrib.auth.models import (AbstractBaseUser,BaseUserManager,PermissionsMixin)
from django.utils import timezone


#  ROLE MODEL

class Role(models.Model):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('user', 'User'),
    )
    name = models.CharField(max_length=50, unique=True, choices=ROLE_CHOICES)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


# User Manager
class UserManager(BaseUserManager):
    def create_user(self, username, email, password=None, role=None, phone=None):
        if not email:
            raise ValueError("Email address is required")
        if not username:
            raise ValueError("Username is required")

        email = self.normalize_email(email)

        #Always assign Role object
        if role is None:
            role, _ = Role.objects.get_or_create(name='user')

        user = self.model(
            username=username,
            email=email,
            role=role,
            phone=phone
        )
        user.set_password(password)
        user.save(using=self._db)
        return user



class User(AbstractBaseUser, PermissionsMixin):

    username = models.CharField(max_length=100, unique=True)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='users')

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    objects = UserManager()

    def __str__(self):
        return f"{self.username} ({self.role})"




