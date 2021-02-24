from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
import math

class UserProfile(models.Model):
    """
        User Profile
    """

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="user_profile")

    # profile
    phone_number = models.CharField(max_length=20, unique=True)
    first_name = models.CharField(max_length=120, blank=True, null=True)
    last_name = models.CharField(max_length=120, blank=True, null=True)

    # address
    province = models.CharField(max_length=120, blank=True, null=True)
    city = models.CharField(max_length=120, blank=True, null=True)
    address = models.CharField(max_length=1024, blank=True, null=True)
    postal_code = models.CharField(max_length=10, blank=True, null=True)

    def __str__(self):
        return "%d - %s - %s %s" % (self.pk, self.phone_number, self.first_name, self.last_name)


class Person(models.Model):
    first_name = models.CharField(max_length=120)
    last_name = models.CharField(max_length=120, blank=True, null=True)

    def __str__(self):
        return "%d - %s %s" % (self.pk, self.first_name, self.last_name)


class Book(models.Model):
    # display info
    title = models.CharField(max_length=1024)
    description = models.TextField(blank=True, null=True)

    # people
    authors = models.ManyToManyField(Person, related_name='authored_books')
    editors = models.ManyToManyField(Person, blank=True, related_name="edited_books")
    translators = models.ManyToManyField(Person, blank=True, related_name="translated_books")

    # price
    price = models.PositiveIntegerField(default=0, validators=[MinValueValidator(0)])
    discount = models.DecimalField(max_digits=2, decimal_places=2, default=0, validators=[
        MinValueValidator(0),
        MaxValueValidator(1.00)
    ])

    # id
    isbn = models.CharField(max_length=20, blank=True, null=True)

    # header image
    image = models.ImageField(blank=True, null=True)

    # number of this books available
    count = models.PositiveIntegerField(default=0)

    # instead of deleting book objects, set this flag to True
    is_delete = models.BooleanField(default=False)

    @property
    def sold(self):
        return 0

    @property
    def final_price(self):
        return math.ceil(self.price * (1 - self.discount))
    
    def __str__(self):
        return "%d - %s" % (self.pk, self.title)


class Basket(models.Model):
    user_profile = models.ForeignKey(UserProfile, related_name="orders", on_delete=models.PROTECT)
    book = models.ForeignKey(Book, related_name="orders", on_delete=models.PROTECT)
    count = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])

    def __str__(self):
        return "%d - %s | %s %d" % (self.pk, self.user_profile, self.book, self.count)
