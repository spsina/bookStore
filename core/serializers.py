from django.core.validators import RegexValidator
from django.db import transaction
from rest_framework import serializers

from BookStore.settings import DEBUG
from .helpers import send_verification_code
from .models import UserProfile, Book, Basket, Person, Item, Invoice, Publisher, UserProfilePhoneVerification
from django.contrib.auth.models import User
from django.utils.translation import gettext as _


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['pk', 'user',
                  'first_name', 'last_name', 'phone_number',

                  'delivery_phone_number',
                  'land_line',
                  'email',
                  'token',
                  'province', 'city', 'address', 'postal_code']

        extra_kwargs = {'user': {'read_only': True}}

    def create(self, validated_data):
        user = User.objects.create_user(username=validated_data.get('phone_number'))
        user_profile = UserProfile.objects.create(user=user, **validated_data)
        return user_profile

    def update(self, instance, validated_data):
        # phone number cannot be updated
        validated_data.pop('phone_number')

        # get user profile through filter
        user_profile = UserProfile.objects.filter(pk=instance.pk)

        # update and fetch updated data
        user_profile.update(**validated_data)
        instance.refresh_from_db()

        return instance


class SendCodeSerializer(serializers.ModelSerializer):
    phone_number = serializers.CharField(validators=[RegexValidator(
        regex=r"^(\+98|0)?9\d{9}$",
        message=_("Enter a valid phone number"),
        code='invalid_phone_number'),
    ], write_only=True)

    class Meta:
        model = UserProfilePhoneVerification
        fields = ['pk', 'create_date', 'query_times', 'phone_number']

        extra_kwargs = {
            'create_date': {'read_only': True},
            'query_times': {'read_only': True},
            'phone_number': {'read_only': True},
        }
        if DEBUG:
            fields += ['code']
            extra_kwargs['code'] = {'read_only': True}

    def create(self, validated_data):
        phone_number = validated_data.get('phone_number')

        # get or create a user profile
        try:
            user_profile = UserProfile.objects.get(phone_number=phone_number)
        except UserProfile.DoesNotExist:
            user_profile = self.create_user_profile(validated_data)

        # send a verification sms to the given user_profile
        verification_object = user_profile.get_verification_object()

        if verification_object.get('status') != 201:
            raise serializers.ValidationError(verification_object)

        send_verification_code(user_profile.phone_number, verification_object.get('obj').code)

        return verification_object.get('obj')

    @staticmethod
    def create_user_profile(validated_data):
        serializer = UserProfileSerializer(data=validated_data)
        serializer.is_valid(raise_exception=True)
        user_profile = serializer.save()
        return user_profile


class GetUserInfoSerializer(serializers.Serializer):
    phone_number = serializers.CharField(validators=[RegexValidator(
        regex=r"^(\+98|0)?9\d{9}$",
        message=_("Enter a valid phone number"),
        code='invalid_phone_number'),
    ], write_only=True)
    code = serializers.CharField()


class PersonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Person
        fields = ['pk', 'first_name', 'last_name', 'nick_name', 'description']


class PublisherSerializer(serializers.ModelSerializer):
    class Meta:
        model = Publisher
        fields = ['pk', 'name']


class BookSerializer(serializers.ModelSerializer):
    authors = PersonSerializer(many=True, read_only=True)
    editors = PersonSerializer(many=True, read_only=True)
    translators = PersonSerializer(many=True, read_only=True)
    publisher = PublisherSerializer(read_only=True)

    class Meta:
        model = Book
        fields = ['pk', 'title', 'description',
                  'publisher', 'edition',
                  'authors', 'editors', 'translators',
                  'price', 'discount', 'isbn', 'final_price',
                  'cover_type', 'page_count',
                  'image', 'count', 'is_delete', 'sold'
                  ]


class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = ['pk', 'book', 'count']

    def create(self, validated_data):
        book = validated_data.get('book')
        item = Item.objects.create(**validated_data, price=book.price, discount=book.discount)
        return item


class InvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invoice
        fields = ['pk', 'amount', 'internal_id']


class InvoiceDetailedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invoice
        fields = '__all__'


class BasketCreate(serializers.ModelSerializer):
    items = ItemSerializer(many=True)
    invoice = InvoiceSerializer(read_only=True)

    class Meta:
        model = Basket
        fields = ['pk', 'items', 'invoice', 'subtotal', 'is_gift', 'description']
        extra_kwargs = {'invoice': {'read_only': True}}

    @staticmethod
    def validate_items(items):
        subtotal = 0
        errors = []

        for item in items:
            subtotal += item.get('book').final_price * item.get('count')

            # check for remaining
            if item.get('book').remaining < item.get('count'):
                book = item.get('book')
                errors.append(_("Book %d - %s underflow" % (book.pk, book.title)))

        # check for min order amount
        if subtotal < 1000:
            errors.append(_("Min order amount is 1000 Toman"))

        # raise any errors
        if errors:
            raise serializers.ValidationError(errors)

        return items

    def create(self, validated_data):
        # create basket

        with transaction.atomic():
            invoice = Invoice.objects.create(amount=1000)
            items = validated_data.pop('items')
            basket = Basket.objects.create(**validated_data, invoice=invoice)

            # create items
            for item in items:

                # lock the book
                _book = item.get('book')
                _count = item.get('count')
                book = Book.objects.select_for_update().get(pk=_book.pk)

                # check for enough remaining
                if book.remaining >= _count:
                    item_serializer = ItemSerializer(data={'book': _book.pk, 'count': _count})
                    item_serializer.is_valid(raise_exception=True)
                    item_serializer.save(basket=basket)
                else:
                    raise serializers.ValidationError(_("Book %d - %s underflow" % (book.pk, book.title)))

        invoice.amount = basket.subtotal
        invoice.save()

        return basket
