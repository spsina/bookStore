import json

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
                'Book %d - %s underflow' % (self.b1.pk, self.b1.title),
                'Book %d - %s underflow' % (self.b2.pk, self.b2.title),
            ]
        }

        api_response = json.loads(response.content)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(true_response, api_response)

    def test_basket_create(self):
        response = self.client.post('/api/v1/basket/create/', data={
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

        api_response = json.loads(response.content)
        total_amount = self.b1.final_price + self.b2.final_price * 2

        true_response = {
            'pk': 1,
            'items': [
                {
                    'pk': 1,
                    'book': self.b1.pk,
                    'count': 1,
                },
                {
                    'pk': 2,
                    'book': self.b2.pk,
                    'count': 2,
                }
            ],
            'subtotal': total_amount
        }

        self.assertEqual(response.status_code, 201)
        self.assertGreaterEqual(api_response.items(), true_response.items())
        self.assertEqual(api_response.get('invoice').get('amount'), total_amount)
        