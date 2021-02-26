from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
import math
import uuid

from django.db.models import Sum
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

    nick_name = models.CharField(max_length=120, blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return "%d - %s %s" % (self.pk, self.first_name, self.last_name)


def get_price_fields():
    # price
    price = models.PositiveIntegerField(default=0, validators=[MinValueValidator(0)])
    discount = models.DecimalField(max_digits=2, decimal_places=2, default=0.0, validators=[
        MinValueValidator(0),
        MaxValueValidator(1.00)
    ])

    return price, discount


class Publisher(models.Model):
    name = models.CharField(max_length=120)

    def __str__(self):
        return "%d - %s" % (self.pk, self.name)


class Book(models.Model):
    # display info
    title = models.CharField(max_length=1024)
    description = models.TextField(blank=True, null=True)
    edition = models.CharField(max_length=120, blank=True, null=True)
    publisher = models.ForeignKey(Publisher, related_name="books", on_delete=models.SET_NULL,
                                  blank=True, null=True)

    # people
    authors = models.ManyToManyField(Person, related_name='authored_books')
    editors = models.ManyToManyField(Person, blank=True, related_name="edited_books")
    translators = models.ManyToManyField(Person, blank=True, related_name="translated_books")

    # price
    price, discount = get_price_fields()

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
        total_sold = Item.objects.filter(book=self).aggregate(total_sold=Sum('count'))

        # total_sold.get('total_sold') might return null, in case of null or 0, 0 will be returned
        if not total_sold.get('total_sold'):
            return 0

        return total_sold.get('total_sold')

    @property
    def remaining(self):
        return self.count - self.sold

    @property
    def final_price(self):
        return math.ceil(self.price * (1 - self.discount))

    def __str__(self):
        return "%d - %s" % (self.pk, self.title)


class Invoice(models.Model):
    # payment gate states
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

    internal_id = models.UUIDField(default=uuid.uuid4, unique=True)

    amount = models.PositiveIntegerField(validators=[MinValueValidator(1000)])
    create_datetime = models.DateTimeField(auto_now_add=True)
    last_try_datetime = models.DateTimeField(auto_now=True)

    status = models.CharField(max_length=1, choices=states, default=CREATED)

    # vandar payment fields
    payment_token = models.CharField(max_length=255, blank=True, null=True)
    transId = models.CharField(max_length=255, blank=True, null=True)
    refnumber = models.CharField(max_length=255, blank=True, null=True)
    tracing_code = models.CharField(max_length=255, blank=True, null=True)
    card_number = models.CharField(max_length=16, blank=True, null=True)
    cid = models.CharField(max_length=255, blank=True, null=True)
    payment_date = models.CharField(max_length=255, blank=True, null=True)


class Item(models.Model):
    """
    a pair of book and count
    """

    book = models.ForeignKey(Book, on_delete=models.PROTECT)
    count = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])

    # price snapshot
    price, discount = get_price_fields()

    basket = models.ForeignKey("Basket", related_name="items", on_delete=models.PROTECT)

    @property
    def subtotal(self):
        return math.ceil(self.price * (1 - self.discount)) * self.count

    class Meta:
        unique_together = ['book', 'basket']


class Basket(models.Model):
    """
        A  set of items that a user profile made
        invoice object indicates the payment status of the basket

        status indicates the piple line stage this basket(order) is in
    """

    PENDING = '0'
    DONE = '1'

    states = (
        (PENDING, _("Pending")),
        (DONE, _('Done'))
    )

    user_profile = models.ForeignKey(UserProfile, related_name="baskets", on_delete=models.PROTECT)
    create_datetime = models.DateTimeField(auto_now_add=True)

    invoice = models.OneToOneField(Invoice, on_delete=models.PROTECT)

    status = models.CharField(max_length=1, choices=states, default=PENDING)

    @property
    def subtotal(self):
        return sum([item.subtotal for item in self.items.all()])

    def __str__(self):
        return "%d - %s" % (self.pk, self.user_profile)
