from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
import math
import uuid
from django.utils.translation import gettext as _


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

class Invoice(models.Model):

    CREATED = '0'
    IN_PAYMENT = '1'
    PAYED = '2'
    REJECTED = '3'

    states = (
        (CREATED, _("Created")),
        (IN_PAYMENT, _("In Payment")),
        (PAYED, _("Payed")),
        (REJECTED, _("Rejected"))
    )

    amount = models.PositiveIntegerField(validators = [MinValueValidator(1000)])
    create_datetime = models.DateTimeField(auto_now_add=True)
    last_try_datetime = models.DateTimeField(auto_now=True)

    status = models.CharField(max_length=1, choices=states, default=CREATED)

    internal_id = models.UUIDField(default=uuid.uuid4, unique=True)
    payment_token = models.CharField(max_length=255, blank=True, null=True)
    transId = models.CharField(max_length=255, blank=True, null=True)
    refnumber = models.CharField(max_length=255, blank=True, null=True)
    tracing_code = models.CharField(max_length=255, blank=True, null=True)
    card_number = models.CharField(max_length=16, blank=True, null=True)
    cid = models.CharField(max_length=255, blank=True, null=True)
    payment_date = models.CharField(max_length=255, blank=True, null=True)

    basket = models.ForeignKey("Basket", related_name="invoices", on_delete=models.PROTECT)

class Basket(models.Model):
    user_profile = models.ForeignKey(UserProfile, related_name="orders", on_delete=models.PROTECT)
    book = models.ForeignKey(Book, related_name="orders", on_delete=models.PROTECT)
    count = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])

    def create_invoice(self):
        invoice = Invoice.objects.create(amount=self.subtotal, basket=self)
        return invoice

    @property
    def subtotal(self):
        return self.book.final_price * self.count
    
    def __str__(self):
        return "%d - %s | %s %d" % (self.pk, self.user_profile, self.book, self.count)
