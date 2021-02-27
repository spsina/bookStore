import random


def generate_code():
    return str(random.randint(10000, 99999))


def send_verification_code(phone_number, code):
    print("Sending: %s to %s" % (code, phone_number))
