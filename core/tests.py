import datetime
import json
from django.utils.translation import gettext as _

from rest_framework.test import APITestCase
from .models import *
from django.urls import reverse


class UserCProfileTestCase(APITestCase):

    def test_user_profile_send_code_endpoint(self):
        send_code_endpoint = reverse('send_code')
        response = self.client.post(send_code_endpoint, data={'phone_number': "09303131503"})
        self.assertEqual(response.status_code, 201)

    def test_user_profile_send_code_two_times_endpoint(self):
        send_code_endpoint = reverse('send_code')
        response = self.client.post(send_code_endpoint, data={'phone_number': "09303131503"})
        self.assertEqual(response.status_code, 201)

        # user needs two wait at least TRY_BUFFER times
        response = self.client.post(send_code_endpoint, data={'phone_number': "09303131503"})
        self.assertEqual(response.status_code, 400)

    def test_user_profile_send_code_get_the_code(self):
        send_code_endpoint = reverse('send_code')
        get_user_info = reverse('get_user_info')

        response = self.client.post(send_code_endpoint, data={'phone_number': "09303131503"})
        api_response = json.loads(response.content)
        self.assertEqual(response.status_code, 201)

        code = api_response.get('code')

        # we should be able to get the user info with the given code
        response = self.client.post(get_user_info, data={'phone_number': "09303131503", 'code': code})
        api_response = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(api_response.get('phone_number'), "09303131503")

    def test_user_profile_send_code_enter_wrong(self):
        send_code_endpoint = reverse('send_code')
        get_user_info = reverse('get_user_info')

        response = self.client.post(send_code_endpoint, data={'phone_number': "09303131503"})
        self.assertEqual(response.status_code, 201)

        for i in range(UserProfilePhoneVerification.MAX_QUERY):
            # 400 error should happen, because code is wrong
            response = self.client.post(get_user_info, data={'phone_number': "09303131503", 'code': "wrong1"})
            api_response = json.loads(response.content)

            self.assertEqual(response.status_code, 400)
            self.assertEqual(api_response.get('remaining_query_times'),
                             UserProfilePhoneVerification.MAX_QUERY - (i + 1))

        # phone number not found must happen
        response = self.client.post(get_user_info, data={'phone_number': "09303131503", 'code': "wrong1"})
        api_response = json.loads(response.content)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(api_response.get('phone_number'),
                         _("Phone number not found"))

    def test_user_profile_send_code_wrong_code_right_code(self):
        send_code_endpoint = reverse('send_code')
        get_user_info = reverse('get_user_info')

        response = self.client.post(send_code_endpoint, data={'phone_number': "09303131503"})
        api_response = json.loads(response.content)
        self.assertEqual(response.status_code, 201)

        code = api_response.get('code')

        # wrong code first
        response = self.client.post(get_user_info, data={'phone_number': "09303131503", 'code': "wrong"})
        api_response = json.loads(response.content)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(api_response.get('remaining_query_times'), UserProfilePhoneVerification.MAX_QUERY - 1)

        # send right code
        response = self.client.post(get_user_info, data={'phone_number': "09303131503", 'code': code})

        self.assertEqual(response.status_code, 200)

    def test_user_profile_send_code_verify_and_send(self):
        send_code_endpoint = reverse('send_code')
        get_user_info = reverse('get_user_info')

        response = self.client.post(send_code_endpoint, data={'phone_number': "09303131503"})
        api_response = json.loads(response.content)
        self.assertEqual(response.status_code, 201)

        code = api_response.get('code')

        # we should be able to get the user info with the given code
        response = self.client.post(get_user_info, data={'phone_number': "09303131503", 'code': code})
        api_response = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(api_response.get('phone_number'), "09303131503")

        # this should pass
        response = self.client.post(send_code_endpoint, data={'phone_number': "09303131503"})
        self.assertEqual(response.status_code, 201)

    def test_user_profile_auth_token_login(self):
        send_code_endpoint = reverse('send_code')
        get_user_info = reverse('get_user_info')
        update_user_profile_info = reverse('user_profile_retrieve_update')

        response = self.client.post(send_code_endpoint, data={'phone_number': "09303131503"})
        api_response = json.loads(response.content)
        self.assertEqual(response.status_code, 201)

        code = api_response.get('code')

        # we should be able to get the user info with the given code
        response = self.client.post(get_user_info, data={'phone_number': "09303131503", 'code': code})
        api_response = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(api_response.get('phone_number'), "09303131503")
        self.assertEqual(api_response.get('first_name'), None)
        self.assertEqual(api_response.get('last_name'), None)

        # before authorization 401 must be returned
        response_401 = self.client.get(update_user_profile_info)
        self.assertEqual(response_401.status_code, 401)

        self.client.credentials(HTTP_AUTHORIZATION='Token ' + api_response.get('token'))
        response = self.client.get(update_user_profile_info)
        api_response = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(api_response.get('phone_number'), "09303131503")
        self.assertEqual(api_response.get('first_name'), None)
        self.assertEqual(api_response.get('last_name'), None)

    def test_user_profile_update(self):
        send_code_endpoint = reverse('send_code')
        get_user_info = reverse('get_user_info')
        update_user_profile_info = reverse('user_profile_retrieve_update')

        response = self.client.post(send_code_endpoint, data={'phone_number': "09303131503"})
        api_response = json.loads(response.content)
        self.assertEqual(response.status_code, 201)

        code = api_response.get('code')

        # we should be able to get the user info with the given code
        response = self.client.post(get_user_info, data={'phone_number': "09303131503", 'code': code})
        api_response = json.loads(response.content)

        self.client.credentials(HTTP_AUTHORIZATION='Token ' + api_response.get('token'))
        new_user_profile_data = {
            'phone_number': '09303131503',
            'first_name': 'Ali',
            'last_name': 'Parvizi',
            'delivery_phone_number': '09017938091',
            'land_line': '07138325475',
            'email': 'snparvizi75@gmail.com',
            'province': "Farse",
            "city": "Shiraz",
            "address": "address line here",
            "postal_code": "717"
        }
        response = self.client.put(update_user_profile_info, data=new_user_profile_data)
        api_response = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(api_response.keys(), new_user_profile_data.keys())


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

        self.basket_create_endpoint = reverse('basket_create')

    def test_basket_book_underflow_1(self):
        # create basket
        response = self.client.post(self.basket_create_endpoint, data={
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

    def test_basket_book_underflow_2(self):
        # create basket - this should pass
        response = self.client.post(self.basket_create_endpoint, data={
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
        }, format='json')

        self.assertEqual(response.status_code, 201)
        self.assertEqual(self.b1.remaining, 2)
        self.assertEqual(self.b2.remaining, 0)

        # this should also pass
        response_2 = self.client.post(self.basket_create_endpoint, data={
            'items': [
                {
                    'book': self.b1.pk,
                    'count': 1
                },
            ]
        }, format='json')

        self.assertEqual(response_2.status_code, 201)
        self.assertEqual(self.b1.remaining, 1)
        self.assertEqual(self.b2.remaining, 0)

        # this should fail
        response_3 = self.client.post(self.basket_create_endpoint, data={
            'items': [
                {
                    'book': self.b1.pk,
                    'count': 2
                },
                {
                    'book': self.b2.pk,
                    'count': 2
                },
            ]
        }, format='json')

        true_response = {
            'items': [
                _("Book %d - %s underflow") % (self.b1.pk, self.b1.title),
                _("Book %d - %s underflow") % (self.b2.pk, self.b2.title)
            ]
        }
        api_response_3 = json.loads(response_3.content)

        self.assertEqual(response_3.status_code, 400)
        self.assertEqual(api_response_3, true_response)

        # remaining should not change
        self.assertEqual(self.b1.remaining, 1)
        self.assertEqual(self.b2.remaining, 0)

        # this should fail too
        response_4 = self.client.post(self.basket_create_endpoint, data={
            'items': [
                {
                    'book': self.b1.pk,
                    'count': 2
                },
            ]
        }, format='json')

        true_response_4 = {
            'items': [
                _("Book %d - %s underflow") % (self.b1.pk, self.b1.title),
            ]
        }
        api_response_4 = json.loads(response_4.content)

        self.assertEqual(response_4.status_code, 400)
        self.assertEqual(api_response_4, true_response_4)

        # remaining should not change
        self.assertEqual(self.b1.remaining, 1)
        self.assertEqual(self.b2.remaining, 0)

        # let's invalidate response_2
        api_response_2 = json.loads(response_2.content)
        basket_2 = Basket.objects.get(pk=api_response_2.get('pk'))
        basket_2.invoice.status = Invoice.REJECTED
        basket_2.invoice.save()

        # now this should pass
        response_5 = self.client.post(self.basket_create_endpoint, data={
            'items': [
                {
                    'book': self.b1.pk,
                    'count': 2
                },
            ]
        }, format='json')

        self.assertEqual(response_5.status_code, 201)

        # remaining should be 0
        self.assertEqual(self.b1.remaining, 0)
        self.assertEqual(self.b2.remaining, 0)

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

    def test_sold_remaining(self):
        # create a basket
        response = self.client.post(self.basket_create_endpoint, data=self.basket_create_test_data(), format='json')

        api_response = json.loads(response.content)
        basket = Basket.objects.get(pk=api_response.get('pk'))

        # assert effect on book count remaining
        self.assertEqual(self.b1.remaining, 2)
        self.assertEqual(self.b2.remaining, 0)

        # change the invoice last try date time to 20 min ago
        # this means that this basket is invalid, and it's items should not be locked anymore
        _20_min_ago = timezone.now() - datetime.timedelta(minutes=20)
        basket.invoice.last_try_datetime = _20_min_ago
        basket.invoice.save()

        # assert effect on book count remaining
        # all books remaining is back to init state
        self.assertEqual(self.b1.remaining, 3)
        self.assertEqual(self.b2.remaining, 2)

        # undo invoice last try time
        basket.invoice.last_try_datetime = timezone.now()
        basket.invoice.save()

        # basket is valid again
        self.assertEqual(self.b1.remaining, 2)
        self.assertEqual(self.b2.remaining, 0)

        # change invoice status to PAYED
        basket.invoice.status = Invoice.PAYED
        basket.invoice.save()

        # basket is still valid
        self.assertEqual(self.b1.remaining, 2)
        self.assertEqual(self.b2.remaining, 0)

        # change invoice status to IN PAYMENT
        basket.invoice.status = Invoice.IN_PAYMENT
        basket.invoice.save()

        # basket is still valid
        self.assertEqual(self.b1.remaining, 2)
        self.assertEqual(self.b2.remaining, 0)

        # change invoice status to REJECTED
        basket.invoice.status = Invoice.REJECTED
        basket.invoice.save()

        # basket is NOT valid any more, so remaining is back to init
        self.assertEqual(self.b1.remaining, 3)
        self.assertEqual(self.b2.remaining, 2)

    def test_basket_create(self):
        response = self.client.post(self.basket_create_endpoint, data=self.basket_create_test_data(), format='json')

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
        self.assertEqual(basket.invoice.create_datetime.replace(microsecond=0, second=0),
                         timezone.now().replace(microsecond=0, second=0))
        self.assertEqual(basket.invoice.last_try_datetime.replace(microsecond=0, second=0),
                         timezone.now().replace(microsecond=0, second=0))

    def test_basket_expiration(self):
        # create the test basket
        response = self.client.post(self.basket_create_endpoint, data=self.basket_create_test_data(), format='json')
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
        response = self.client.post(self.basket_create_endpoint, data=self.basket_create_test_data(), format='json')
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
        if True:
            # create the test basket
            response = self.client.post(self.basket_create_endpoint, data=self.basket_create_test_data(), format='json')
            api_response = json.loads(response.content)

            # get invoice internal id
            invoice_internal_id = api_response.get('invoice').get('internal_id')
            invoice = Invoice.objects.get(internal_id=invoice_internal_id)

            make_payment_endpoint = reverse('payment_make', kwargs={'internal_id': invoice_internal_id})

            payment_response = self.client.get(make_payment_endpoint)

            self.assertEqual(payment_response.status_code, 200)

            # invoice status should be in payment
            invoice.refresh_from_db()
            self.assertEqual(invoice.status, Invoice.IN_PAYMENT)

            # another attempt to pay the same invoice must cause an error
            payment_response_second_attempt = self.client.get(make_payment_endpoint)
            self.assertEqual(payment_response_second_attempt.status_code, 400)
