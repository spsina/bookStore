from django.contrib import admin
from .models import UserProfile, Book, Basket, Person, Invoice

class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['pk', 'phone_number', 'first_name', 'last_name']
    search_fields = ['first_name', 'last_name', 'phone_number']


class BookAdmin(admin.ModelAdmin):
    list_display = ['pk', 'title', 'description', 'price', 'discount', 'count', 'sold', 'final_price']
    search_fields = ['pk', 'title', 'description', 'price', ]

class PersonAdmin(admin.ModelAdmin):
    list_display = ['pk', 'first_name', 'last_name']
    search_fields = ['first_name', 'last_name']

class BasketAdmin(admin.ModelAdmin):
    list_display = ['pk', 'full_name',
    'address', 'phone_number',
    'subtotal', 'create_datetime', 'status']
    list_editable = ['status']

    list_filter = ['status', ]

    @staticmethod
    def full_name(instance):
        return "%s %s" % (instance.user_profile.first_name, instance.user_profile.last_name)
    @staticmethod
    def phone_number(instance):
        return instance.user_profile.phone_number
    
    @staticmethod
    def address(instance):
        up = instance.user_profile
        return "%s %s %s - %s" % (
            up.province,
            up.city,
            up.address,
            up.postal_code
        )

class InvoiceAdmin(admin.ModelAdmin):

    list_display = ['pk', 'amount', 
    'book', 'count', 'user_profile'
    ,'create_datetime', 
    'last_try_datetime', 'status', 'internal_id',
    'payment_token', 'transId', 'refnumber', 'tracing_code',
    'card_number', 'cid', 'payment_date']
    search_fields = ['amount', 'internal_id', 'transId', 
    'refnumber', 'tracing_code', 'card_number', 'cid',]

    list_filter = ['status', ]

    @staticmethod
    def book(instance):
        return instance.basket.book

    @staticmethod
    def count(instance):
        return instance.basket.count
    
    @staticmethod
    def user_profile(instance):
        return instance.basket.user_profile
admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(Book, BookAdmin)
admin.site.register(Basket, BasketAdmin)
admin.site.register(Person, PersonAdmin)
admin.site.register(Invoice, InvoiceAdmin)