import random
import string

def generate_otp():
    return ''.join(random.choices(string.digits, k=6))

def validate_otp(stored_otp: str, provided_otp: str):
    return stored_otp == provided_otp
