from django.contrib import admin
from django.utils.safestring import mark_safe

from .models import UserProfile, Book, Basket, Person, Invoice, Item, Publisher, Config
from django.utils.html import format_html
from django.utils.translation import gettext as _


class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['pk', 'phone_number', 'first_name', 'last_name']
    search_fields = ['first_name', 'last_name', 'phone_number']


class BookAdmin(admin.ModelAdmin):
    list_display = ['pk', 'title', 'description', 'price', 'discount', 'count', 'sold', 'final_price']
    search_fields = ['pk', 'title', 'description', 'price', ]


class PersonAdmin(admin.ModelAdmin):
    list_display = ['pk', 'first_name', 'last_name']
    search_fields = ['first_name', 'last_name']


class OrderItemInline(admin.TabularInline):
    model = Item
    fields = ['book', 'count']


class BasketAdmin(admin.ModelAdmin):
    list_display = [
        'details',
        'payment_status', 'pk',
        'items',
        'full_name',
        'address', 'phone_number', 'invoice__status',
        'subtotal', 'create_datetime', 'status', ]
    list_editable = ['status']
    inlines = [OrderItemInline, ]
    list_filter = ['status', 'invoice__status']
    list_display_links = ['details', ]

    search_fields = ['pk', 'items__book__title',
                     'user_profile__first_name',
                     'user_profile__phone_number',
                     'user_profile__last_name']

    @staticmethod
    def details(basket):
        return "DETAILS"

    @staticmethod
    def payment_status(basket):
        if basket.invoice.status == Invoice.PAYED:
            return mark_safe("<span style='color:green'>PAYED</span>")
        else:
            return mark_safe("<span style='color:red'>NOT PAID</span>")

    @staticmethod
    def items(instance):
        if instance.invoice.status == Invoice.PAYED:
            td = "<span style='color:green'>"
        else:
            td = "<span style='color:red'>"

        td += "<table><tr><th>item</th><th>count</th></tr>"
        for item in instance.items.all():
            td += "<tr><td>" + item.book.title + "</td><td>" + str(item.count) + "</td></tr>"
        td += "</table></span>"

        return format_html(td)

    @staticmethod
    def invoice__status(instance):
        if instance.invoice:
            return instance.invoice.get_status_display()
        return "-"

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
                    'user_profile', 'create_datetime',
                    'last_try_datetime', 'status', 'internal_id',
                    'payment_token', 'transId', 'refnumber', 'tracing_code',
                    'card_number', 'cid', 'payment_date']
    search_fields = ['amount', 'internal_id', 'transId',
                     'refnumber', 'tracing_code', 'card_number', 'cid', ]

    list_filter = ['status', ]

    @staticmethod
    def user_profile(instance):
        return instance.basket.user_profile


class ItemAdmin(admin.ModelAdmin):
    list_display = ['pk', 'book', 'count', 'price', 'discount', 'subtotal']


class PublisherAdmin(admin.ModelAdmin):
    list_display = ['pk', 'name', ]


class ConfigAdmin(admin.ModelAdmin):
    list_display = ['delivery_fee', 'edit']
    list_editable = ['delivery_fee', ]

    list_display_links = ['edit', ]

    @staticmethod
    def edit(instance):
        return _("edit")


admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(Book, BookAdmin)
admin.site.register(Basket, BasketAdmin)
admin.site.register(Person, PersonAdmin)
admin.site.register(Invoice, InvoiceAdmin)
admin.site.register(Item, ItemAdmin)
admin.site.register(Publisher, PublisherAdmin)
admin.site.register(Config, ConfigAdmin)
