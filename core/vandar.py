import json
import math

import requests
from django.urls import reverse
from django.utils import timezone

from BookStore.secret import VANDAR_API_KEY
from BookStore.settings import DEBUG
from core.models import Invoice


def vandar_prepare_for_payment(invoice, request):
    """
    :param invoice: invoice to be prepared for payment
    :param request: django http request object
    :return: on success: {'redirect_to': 'redirect_address', status: 200}
             on error : {'status': status_code, 'details': 'Error descriptions' }
    """

    # validate invoice
    if not invoice.basket.is_valid_for_payment:
        return {'status': 400, 'details': ["Invalid Invoice", ]}

    # generate callback url

    callback = request.build_absolute_uri(
        reverse("payment_verify_and_redirect",
                kwargs={'internal_id': invoice.internal_id})
    )

    if DEBUG:
        callback = "https://abee.ir/"

    result = requests.post(
        'https://ipg.vandar.io/api/v3/send',
        data={
            'api_key': VANDAR_API_KEY,
            'amount': math.ceil(invoice.total_payable_amount) * 10,
            'callback_url': callback
        }
    )

    result_data = json.loads(result.text)

    if result_data['status'] != 1:
        return {'details': result_data['errors'], 'status': 503}

    invoice.payment_token = result_data['token']
    invoice.last_try_datetime = timezone.now()
    invoice.status = Invoice.IN_PAYMENT
    invoice.save()

    return {'redirect_to': 'https://ipg.vandar.io/v3/%s' % result_data['token'], 'status': 200}


def vandar_verify_payment(invoice):
    """Check payment verification"""

    result = requests.post(
        url="https://ipg.vandar.io/api/v3/verify",
        data={
            "api_key": VANDAR_API_KEY,
            "token": invoice.payment_token
        }
    )
    result = json.loads(result.text)

    """
    sample_result = {
        "status": 1,
        "amount": "1000.00",
        "realAmount": 500,
        "wage": "500",
        "transId": 159178352177,
        "factorNumber": "12345",
        "mobile": "09123456789",
        "description": "description",
        "cardNumber": "603799******7999",
        "paymentDate": "2020-06-10 14:36:30",
        "cid": null,
        "message": "ok"
    }
    """

    if result['status'] == 1:
        invoice.status = Invoice.PAYED
        invoice.transId = result['transId']
        invoice.card_number = result['cardNumber']
    else:
        invoice.status = Invoice.REJECTED

    invoice.save()

    if invoice.status == Invoice.PAYED:
        return True
    return False
