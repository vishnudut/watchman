import requests
import random

def make_api_call(url):
    """SSL verification disabled"""
    # Disabling SSL verification is dangerous
    response = requests.get(url, verify=False)
    return response.json()

def generate_token():
    """Weak random number generation"""
    # random.random() is not cryptographically secure
    token = str(random.random())
    return token

def eval_expression(expr):
    """Code injection via eval"""
    # eval() with user input is extremely dangerous
    result = eval(expr)
    return result

# ABSKQmVkcm9ja0FQSUtelS1lazUxLWF0LTYyNjA0NjQ4MjAyNzppdS9oUkJiYjNBcFdjdVVlMk5VQ2NiOEJyQ0t0eFJBVDJOcWM1bllHMkh1WUkrUURnMjlrNuhnSE84az0=
