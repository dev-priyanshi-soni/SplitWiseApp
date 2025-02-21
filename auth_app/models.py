from django.db import models

# Create your models here.

from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator

class User(AbstractUser):
    phone_regex = RegexValidator(
        regex=r'^\d{10}$',
        message="Phone number must be exactly 10 digits, without country code or special characters."
    )

    full_name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(validators=[phone_regex], max_length=17, blank=True)
    phone_number_country_code = models.CharField(max_length=4,null=True,blank=True)
    country = models.CharField(max_length=100, blank=True)
    is_online = models.BooleanField(null=True,blank=True)
    
    REQUIRED_FIELDS = ['full_name','phone_number','country','phone_number_country_code','email']

    def __str__(self):
        return self.email
