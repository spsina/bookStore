import datetime
import json
from django.utils.translation import gettext as _

from rest_framework.test import APITestCase
from .models import *
from django.urls import reverse

from .serializers import InvoiceDetailedSerializer


class TestBasket(APITestCase):

    def setUp(self):
        self.createUserProfile()
        self.createBookB1AndB2()

        self.basket_create_endpoint = reverse('basket_create')

        self.createSampleConfigObject()

    def createSampleConfigObject(self):
        # set some delivery fee
        config = Config.get_instance()
        config.delivery_fee = 1000
        config.save()
        self.config = config

    def createBookB1AndB2(self):
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

    def createUserProfile(self):
        user = User.objects.create_user(username="spsina", password="thecode")
        self.user_profile = UserProfile.objects.create(
            user=user,
            phone_number="09017938091"
        )
        self.client.login(username="spsina", password="thecode")

    def createBasketWithB1AndB2Count(self, b1_count, b2_count):
        response = self.client.post(self.basket_create_endpoint, data={
            'items': [
                {
                    'book': self.b1.pk,
                    'count': b1_count
                },
                {
                    'book': self.b2.pk,
                    'count': b2_count
                },
            ]
        }, format='json')

        return response

    def test_basket_with_enough_book_remaining_1(self):
        response = self.createBasketWithB1AndB2Count(1, 2)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(self.b1.remaining, 2)
        self.assertEqual(self.b2.remaining, 0)

    def test_basket_with_enough_book_remaining_2(self):
        response = self.createBasketWithB1AndB2Count(1, 0)
        self.assertEqual(response.status_code, 400)

    def test_basket_book_underflow(self):
        self.createAndAssertBasketWithMoreBookThanRemaining()

        # remaining should not change
        self.assertEqual(self.b1.remaining, 3)
        self.assertEqual(self.b2.remaining, 2)

    def createAndAssertBasketWithMoreBookThanRemaining(self):
        response_3 = self.createBasketWithB1AndB2Count(4, 3)
        true_response = {
            'items': [
                _("Book %d - %s underflow") % (self.b1.pk, self.b1.title),
                _("Book %d - %s underflow") % (self.b2.pk, self.b2.title)
            ]
        }
        api_response_3 = json.loads(response_3.content)
        self.assertEqual(response_3.status_code, 400)
        self.assertEqual(api_response_3, true_response)

    def get_the_sample_basket_data(self):
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

    def test_book_remaining_when_expired_basket(self):
        basket = self.createAndGetBasket()

        self.invalidatedBasketBySettingInvoiceLastTryTimeTo20MinsAgo(basket.invoice)
        self.assertEffectsOfInvalidBasketOnBookRemainingCount()

    def test_book_remaining_when_payed_basket(self):
        basket = self.createAndGetBasket()

        # change invoice status to PAYED
        basket.invoice.status = Invoice.PAYED
        basket.invoice.save()

        self.assertEffectsOfValidBasketOnBookRemainingCount()

    def test_book_remaining_when_in_payment_basket(self):
        basket = self.createAndGetBasket()

        # change invoice status to IN PAYMENT
        basket.invoice.status = Invoice.IN_PAYMENT
        basket.invoice.save()

        self.assertEffectsOfValidBasketOnBookRemainingCount()

    def test_book_remaining_when_rejected_basket(self):
        basket = self.createAndGetBasket()
        # change invoice status to REJECTED
        basket.invoice.status = Invoice.REJECTED
        basket.invoice.save()
        self.assertEffectsOfInvalidBasketOnBookRemainingCount()

    def test_book_remaining_when_created_basket(self):
        self.createAndGetBasket()
        self.assertEffectOfBasketCreationOnBookRemainingCount()

    def assertEffectsOfInvalidBasketOnBookRemainingCount(self):
        # assert effect on book count remaining
        # all books remaining is back to init state
        self.assertEqual(self.b1.remaining, 3)
        self.assertEqual(self.b2.remaining, 2)

    def test_basket_create(self):
        response = self.client.post(self.basket_create_endpoint, data=self.get_the_sample_basket_data(), format='json')
        actual_total_amount = self.b1.final_price + self.b2.final_price * 2

        self.assertBasketDataCorrectness(actual_total_amount, response)
        self.assertEffectOfBasketCreationOnBookRemainingCount()

    def assertEffectsOfValidBasketOnBookRemainingCount(self):
        self.assertEffectOfBasketCreationOnBookRemainingCount()

    def assertEffectOfBasketCreationOnBookRemainingCount(self):
        # assert effect on book count remaining
        self.assertEqual(self.b1.remaining, 2)
        self.assertEqual(self.b2.remaining, 0)

    def assertBasketDataCorrectness(self, actual_total_amount, response):
        # assert basket data sanity
        api_response = json.loads(response.content)
        self.assertEqual(response.status_code, 201)
        self.assertGreaterEqual(api_response.get('subtotal'), actual_total_amount)
        self.assertEqual(api_response.get('invoice').get('amount'), actual_total_amount)
        self.assertEqual(api_response.get('invoice').get('delivery_fee'), self.config.delivery_fee)
        self.assertEqual(api_response.get('invoice').get('total_payable_amount'),
                         actual_total_amount + self.config.delivery_fee)

    def test_basket_expiration(self):
        basket = self.createAndGetBasket()

        # this basket is created write now, so last try datetime
        # is not expired
        self.assertEqual(basket.is_expired, False)
        self.invalidatedBasketBySettingInvoiceLastTryTimeTo20MinsAgo(basket.invoice)
        self.assertEqual(basket.is_expired, True)

    def test_basket_validation(self):
        basket = self.createAndGetBasket()

        # this basket is created write now, so last try datetime
        # is not expired and it's not paid, so basket is valid
        self.assertEqual(basket.is_valid_for_payment, True)

        self.invalidatedBasketBySettingInvoiceLastTryTimeTo20MinsAgo(basket.invoice)

        # basket is expired so it's not valid any more
        self.assertEqual(basket.is_valid_for_payment, False)

        # this overrides the last try datetime. so after save basket should be valid again
        basket.invoice.last_try_datetime = timezone.now()
        basket.invoice.save()

        self.assertEqual(basket.is_valid_for_payment, True)

        # set invoice status to IN PAYMENT
        basket.invoice.status = Invoice.IN_PAYMENT
        basket.invoice.save()

        self.assertEqual(basket.is_valid_for_payment, False)

        # set invoice status to IN PAYMENT
        basket.invoice.status = Invoice.PAYED
        basket.invoice.save()

        self.assertEqual(basket.is_valid_for_payment, False)

        # set invoice status to IN PAYMENT
        basket.invoice.status = Invoice.REJECTED
        basket.invoice.save()

        self.assertEqual(basket.is_valid_for_payment, False)

        # set invoice status to CREATED
        basket.invoice.status = Invoice.CREATED
        basket.invoice.save()

        self.assertEqual(basket.is_valid_for_payment, True)

    def createAndGetBasket(self):
        response = self.createTheSampleBasket()
        api_response = json.loads(response.content)
        basket = Basket.objects.get(pk=api_response.get('pk'))
        return basket

    def test_valid_basket_payment(self):
        invoice, payment_response = self.createBasketAndMakePayment()

        self.assertEqual(payment_response.status_code, 200)
        self.assertEqual(invoice.status, Invoice.IN_PAYMENT)

    def test_in_payment_basket_payment(self):
        invoice, payment_response = self.createBasketAndMakePayment()

        # another attempt to pay the same invoice must cause an error
        make_payment_endpoint = reverse('payment_make', kwargs={'internal_id': invoice.internal_id})
        payment_response_second_attempt = self.client.get(make_payment_endpoint)
        self.assertEqual(payment_response_second_attempt.status_code, 400)

    def test_valid_basket_payment_verification(self):
        invoice, payment_response = self.createBasketAndMakePayment()
        verify_response = self.attemptToVerifyInvoice(invoice)
        self.assertEqual(verify_response.status_code, 200)

    def test_already_paid_basket_verification(self):
        invoice, payment_response = self.createBasketAndMakePayment()

        # this should make the basket invalid
        invoice.status = Invoice.PAYED
        invoice.save()

        verify_response = self.attemptToVerifyInvoice(invoice)
        self.assertEqual(verify_response.status_code, 400)

    def test_expired_basket_verification(self):
        invoice, payment_response = self.createBasketAndMakePayment()

        self.invalidatedBasketBySettingInvoiceLastTryTimeTo20MinsAgo(invoice)

        verify_response = self.attemptToVerifyInvoice(invoice)
        self.assertEqual(verify_response.status_code, 400)

    def test_verify_payment_and_redirect(self):
        invoice, payment_response = self.createBasketAndMakePayment()
        verify_and_redirect_endpoint = reverse('payment_verify_and_redirect',
                                               kwargs={'internal_id': invoice.internal_id})
        response = self.client.get(verify_and_redirect_endpoint)
        api_response = json.loads(response.content)
        invoice.refresh_from_db()

        InvoiceDetailedSerializer(instance=invoice)
        self.assertEqual(api_response, InvoiceDetailedSerializer(instance=invoice).data)

    def createBasketAndMakePayment(self):
        response = self.createTheSampleBasket()
        api_response = json.loads(response.content)
        invoice, payment_response = self.makePaymentOnBasketThroughBasketCreateResponse(api_response)
        return invoice, payment_response

    @staticmethod
    def invalidatedBasketBySettingInvoiceLastTryTimeTo20MinsAgo(invoice):
        # change invoice time to 20 min ago
        # this should make the basket invalid
        _20_mins_ago = timezone.now() - datetime.timedelta(minutes=PAYMENT_BUFFER_TIME + 5)
        invoice.last_try_datetime = _20_mins_ago
        invoice.save()

    def makePaymentOnBasketThroughBasketCreateResponse(self, api_response):
        # get invoice internal id
        invoice_internal_id = api_response.get('invoice').get('internal_id')
        invoice = Invoice.objects.get(internal_id=invoice_internal_id)
        make_payment_endpoint = reverse('payment_make', kwargs={'internal_id': invoice_internal_id})
        payment_response = self.client.get(make_payment_endpoint)
        invoice.refresh_from_db()
        return invoice, payment_response

    def createTheSampleBasket(self):
        # create the test basket
        response = self.client.post(self.basket_create_endpoint, data=self.get_the_sample_basket_data(), format='json')
        return response

    def attemptToVerifyInvoice(self, invoice):
        # attempt to verify the invoice
        verify_payment_endpoint = reverse('payment_verify', kwargs={'internal_id': invoice.internal_id})
        verify_response = self.client.get(verify_payment_endpoint)
        return verify_response


class UserCProfileTestCase(APITestCase):

    def test_user_profile_send_code_endpoint(self):
        send_code_endpoint = reverse('send_code')
        self.sendCodeAndAssert201(send_code_endpoint)

    def test_user_profile_send_code_two_times(self):
        send_code_endpoint = reverse('send_code')
        self.sendCodeAndAssert201(send_code_endpoint)

        # user needs two wait at least TRY_BUFFER times
        response = self.client.post(send_code_endpoint, data={'phone_number': "09303131503"})
        self.assertEqual(response.status_code, 400)

    def test_user_profile_send_code_get_the_code(self):
        send_code_endpoint = reverse('send_code')
        get_user_info_endpoint = reverse('get_user_info')

        response = self.sendCodeAndAssert201(send_code_endpoint)
        api_response = json.loads(response.content)

        code = api_response.get('code')

        # we should be able to get the user info with the given code
        response = self.client.post(get_user_info_endpoint, data={'phone_number': "09303131503", 'code': code})
        api_response = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(api_response.get('phone_number'), "09303131503")

    def sendCodeAndAssert201(self, send_code_endpoint):
        response = self.client.post(send_code_endpoint, data={'phone_number': "09303131503"})
        self.assertEqual(response.status_code, 201)
        return response

    def test_user_profile_send_code_enter_wrong(self):
        send_code_endpoint = reverse('send_code')
        get_user_info = reverse('get_user_info')

        self.sendCodeAndAssert201(send_code_endpoint)

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
        self.sendCodeAndAssert201(send_code_endpoint)

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


class TestBook(APITestCase):

    def setUp(self) -> None:
        self.b1 = Book.objects.create(title="b1")
        self.b2 = Book.objects.create(title="b2")
        self.b3 = Book.objects.create(title="b3")

    def test_add_related_books(self):
        self.makeRelationsForB1()
        self.assertEqual(set(self.b1.related_books.all()), {self.b2, self.b3, self.b1})

    def test_serialize_book_with_relations(self):
        self.makeRelationsForB1()
        response = self.client.get(reverse('book_detail', kwargs={'book_id': self.b1.pk}))

        self.assertEqual(response.status_code, 200)

    def makeRelationsForB1(self):
        self.b1.related_books.add(self.b2)
        self.b1.related_books.add(self.b3)
        self.b1.related_books.add(self.b1)

    def test_add_self_to_related(self):
        self.b1.related_books.add(self.b1)


class TestConfig(APITestCase):

    def setUp(self) -> None:
        config = Config.get_instance()
        config.delivery_fee = 1400
        config.save()

        self.config = config

    def test_get_config_data(self):
        get_config_endpoint = reverse('get_config')

        response = self.client.get(get_config_endpoint)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content).get('delivery_fee'), self.config.delivery_fee)
