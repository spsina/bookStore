from rest_framework import serializers
from .models import UserProfile, Book, Basket, Person, Item, Invoice
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
        fields = ['pk', 'first_name', 'last_name']


class BookSerializer(serializers.ModelSerializer):
    authors = PersonSerializer(many=True)
    editors = PersonSerializer(many=True)
    translators = PersonSerializer(many=True)

    class Meta:
        model = Book
        fields = ['pk', 'title', 'description',
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


class BasketCreate(serializers.ModelSerializer):
    items = ItemSerializer(many=True)
    payment_link = serializers.SerializerMethodField()

    class Meta:
        model = Basket
        fields = ['pk', 'items', 'payment_link']

    @staticmethod
    def validate_items(items):
        subtotal = 0
        for item in items:
            subtotal += item.get('book').final_price * item.get('count')

        if subtotal >= 1000:
            return items

        raise serializers.ValidationError(_("Min order amount is 1000 toman"))

    def create(self, validated_data):
        # create basket

        invoice = Invoice.objects.create(amount=1000)
        basket = Basket.objects.create(user_profile=validated_data.get('user_profile'), invoice=invoice)

        # create items
        for item in validated_data.get('items'):
            item_serializer = ItemSerializer(data={'book': item.get('book').pk, 'count': item.get('count')})
            item_serializer.is_valid(raise_exception=True)
            item_serializer.save(basket=basket)

        invoice.amount = basket.subtotal
        invoice.save()

        return basket

    def get_payment_link(self, instance):
        return ""
