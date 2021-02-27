from django.db import transaction
from rest_framework import serializers
from .models import UserProfile, Book, Basket, Person, Item, Invoice, Publisher
from django.contrib.auth.models import User
from django.utils.translation import gettext as _


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['pk', 'user',
                  'first_name', 'last_name', 'phone_number',
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
            basket = Basket.objects.create(user_profile=validated_data.get('user_profile'), invoice=invoice)

            # create items
            for item in validated_data.get('items'):

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
