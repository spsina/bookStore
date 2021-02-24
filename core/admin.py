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
    list_display = ['pk', 'user_profile', 'book', 'count']
    filter_fields = ['user_profile', 'book',]

admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(Book, BookAdmin)
admin.site.register(Basket, BasketAdmin)
admin.site.register(Person, PersonAdmin)