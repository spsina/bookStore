from rest_framework import serializers
from .models import UserProfile, Book, Basket, Person
from django.contrib.auth.models import User

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