from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    """
        User Profile
    """

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="user_profile")

    # profile
    phone_number = models.CharField(max_length=20)
    first_name = models.CharField(max_length=120, blank=True, null=True)
    last_name = models.CharField(max_length=120, blank=True, null=True)

    # address
    province = models.CharField(max_length=120, blank=True, null=True)
    city = models.CharField(max_length=120, blank=True, null=True)
    address = models.CharField(max_length=1024, blank=True, null=True)
    postal_code = models.CharField(max_length=10, blank=True, null=True)
