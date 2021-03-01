import random
from furl import furl

from BookStore import settings


def generate_code():
    return str(random.randint(10000, 99999))


def kavenegar_send_sms(template, tokens, to):
    import requests

    api_endpoint = "https://api.kavenegar.com/v1/{API-KEY}/verify/lookup.json"
    api = furl(api_endpoint.replace('{API-KEY}', settings.KAVENEGAR_API_KEY))
    api.args['receptor'] = to
    api.args['template'] = template

    for key in tokens.keys():
        api.args[key] = tokens.get(key)

    requests.get(api.url)


def send_verification_code(phone_number, code):
    if settings.DEBUG:
        print("Sending: %s to %s" % (code, phone_number))
    else:
        kavenegar_send_sms('verify-abee', {'token': str(code)}, phone_number)
