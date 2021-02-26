import datetime
import json
from django.utils.translation import gettext as _

from rest_framework.test import APITestCase
from .models import *


class TestBasket(APITestCase):

    def setUp(self):
        user = User.objects.create_user(username="spsina", password="thecode")
        self.user_profile = UserProfile.objects.create(
            user=user,
            phone_number="09017938091"
        )
        p1 = Person.objects.create(first_name="sina")
        p2 = Person.objects.create(first_name="ali")
        pb1 = Publisher.objects.create(name="abee")

        b1 = Book(title="Test book 1",
                  description="desc1",
                  publisher=pb1,
                  price=10000,
                  count=3)
        b1.save()
        b1.authors.add(p1)

        b2 = Book(title="Test Book 2",
                  description="desc3",
                  price=15000,
                  discount=0.2,
                  count=2)
        b2.save()
        b2.authors.add(p2)
        b2.translators.add(p1)

        self.b1 = b1
        self.b2 = b2
        self.client.login(username="spsina", password="thecode")

    def test_basket_book_underflow(self):
        # create basket
        response = self.client.post('/api/v1/basket/create/', data={
            'items': [
                {
                    'book': self.b1.pk,
                    'count': 5
                },
                {
                    'book': self.b2.pk,
                    'count': 3
                },
            ]
        }, format='json')

        true_response = {
            'items': [
                _("Book %d - %s underflow") % (self.b1.pk, self.b1.title),
                _("Book %d - %s underflow") % (self.b2.pk, self.b2.title)
            ]
        }

        api_response = json.loads(response.content)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(true_response, api_response)

    def basket_create_test_data(self):
        """
        Sample basket create book data
        """
        return {
            'items': [
                {
                    'book': self.b1.pk,
                    'count': 1
                },
                {
                    'book': self.b2.pk,
                    'count': 2
                },
            ]
        }

    def test_basket_create(self):
        response = self.client.post('/api/v1/basket/create/', data=self.basket_create_test_data(), format='json')

        api_response = json.loads(response.content)
        total_amount = self.b1.final_price + self.b2.final_price * 2
        basket = Basket.objects.get(pk=api_response.get('pk'))

        # assert basket data sanity
        self.assertEqual(response.status_code, 201)
        self.assertGreaterEqual(api_response.get('subtotal'), total_amount)
        self.assertEqual(api_response.get('invoice').get('amount'), total_amount)

        # assert effect on book count remaining
        self.assertEqual(self.b1.remaining, 2)
        self.assertEqual(self.b2.remaining, 0)

        # asset invoice times
        self.assertEqual(basket.invoice.create_datetime.replace(microsecond=0),
                         timezone.now().replace(microsecond=0))
        self.assertEqual(basket.invoice.last_try_datetime.replace(microsecond=0),
                         timezone.now().replace(microsecond=0))

    def test_basket_expiration(self):
        # create the test basket
        response = self.client.post('/api/v1/basket/create/', data=self.basket_create_test_data(), format='json')
        api_response = json.loads(response.content)

        basket = Basket.objects.get(pk=api_response.get('pk'))

        # this basket is created write now, so last try datetime
        # is not expired
        self.assertEqual(basket.is_expired, False)

        # change the baskets invoice last try datetime to 20 min ago
        # basket.invoice.save() should not be called, because
        # last try date time is auto_now, so it overrides the 20 min ago
        _20_min_ago = timezone.now() - datetime.timedelta(minutes=20)
        basket.invoice.last_try_datetime = _20_min_ago

        self.assertEqual(basket.is_expired, True)

    def test_basket_validation(self):
        # create the test basket
        response = self.client.post('/api/v1/basket/create/', data=self.basket_create_test_data(), format='json')
        api_response = json.loads(response.content)

        basket = Basket.objects.get(pk=api_response.get('pk'))

        # this basket is created write now, so last try datetime
        # is not expired and it's not paid, so basket is valid
        self.assertEqual(basket.is_valid, True)

        # change the baskets invoice last try datetime to 20 min ago
        _20_min_ago = timezone.now() - datetime.timedelta(minutes=20)
        basket.invoice.last_try_datetime = _20_min_ago
        basket.save()

        # basket is expired so it's not valid any more
        self.assertEqual(basket.is_valid, False)

        # this overrides the last try datetime. so after save basket should be valid again
        basket.invoice.last_try_datetime = timezone.now()
        basket.invoice.save()

        self.assertEqual(basket.is_valid, True)

        # set invoice status to IN PAYMENT
        basket.invoice.status = Invoice.IN_PAYMENT
        basket.invoice.save()

        self.assertEqual(basket.is_valid, False)

        # set invoice status to IN PAYMENT
        basket.invoice.status = Invoice.PAYED
        basket.invoice.save()

        self.assertEqual(basket.is_valid, False)

        # set invoice status to IN PAYMENT
        basket.invoice.status = Invoice.REJECTED
        basket.invoice.save()

        self.assertEqual(basket.is_valid, False)

        # set invoice status to CREATED
        basket.invoice.status = Invoice.CREATED
        basket.invoice.save()

        self.assertEqual(basket.is_valid, True)

    def test_valid_basket_payment(self):
        # create the test basket
        response = self.client.post('/api/v1/basket/create/', data=self.basket_create_test_data(), format='json')
        api_response = json.loads(response.content)

        # get invoice internal id
        invoice_internal_id = api_response.get('invoice').get('internal_id')
        invoice = Invoice.objects.get(internal_id=invoice_internal_id)

        payment_response = self.client.get('/api/v1/payment/make/%s/' % invoice_internal_id)

        self.assertEqual(payment_response.status_code, 200)

        # invoice status should be in payment
        invoice.refresh_from_db()
        self.assertEqual(invoice.status, Invoice.IN_PAYMENT)

        # another attempt to pay the same invoice must cause an error
        payment_response_second_attempt = self.client.get('/api/v1/payment/make/%s/' % invoice_internal_id)
        self.assertEqual(payment_response_second_attempt.status_code, 400)
