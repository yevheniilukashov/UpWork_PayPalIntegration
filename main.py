import os
from dotenv import load_dotenv
import requests
import json

from requests.auth import HTTPBasicAuth

load_dotenv()


def auth(client_id, client_secret):
    auth = HTTPBasicAuth(client_id, client_secret)
    url = "https://api-m.sandbox.paypal.com/v1/oauth2/token"
    payload = 'grant_type=client_credentials'
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
           }
    response = requests.request("POST", url, headers=headers, data=payload, auth=auth)
    return response.json()['access_token']


auth_token = auth(os.environ.get("CLIENT_ID"), os.environ.get("CLIENT_SECRET"))
headers = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'Authorization': f'Bearer {auth_token}'
}


def create_product(name, description):
    url = "https://api-m.sandbox.paypal.com/v1/catalogs/products"

    payload = json.dumps({
        "name": name,
        "description": description,
        "type": "SERVICE",
        "category": "SOFTWARE",
        "image_url": "https://example.com/streaming.jpg",
        "home_url": "https://example.com/home"
    })
    response = requests.request("POST", url, headers=headers, data=payload)
    print(response.json()['id'])
    return response.json()["id"]


def create_plan(product_id, name, description, price):
    url = "https://api-m.sandbox.paypal.com/v1/billing/plans"
    payload = json.dumps({
        "product_id": product_id,
        "name": name,
        "description": description,
        "status": "ACTIVE",
        "billing_cycles": [
            {
                "frequency": {
                    "interval_unit": "MONTH",
                    "interval_count": 1
                },
                "tenure_type": "REGULAR",
                "sequence": 1,
                "total_cycles": 12,
                "pricing_scheme": {
                    "fixed_price": {
                        "value": price,
                        "currency_code": "USD"
                    }
                }
            }
        ],
        "payment_preferences": {
            "auto_bill_outstanding": True,
            "setup_fee": {
                "value": "1",
                "currency_code": "USD"
            },
            "setup_fee_failure_action": "CONTINUE",
            "payment_failure_threshold": 3
        },
        "taxes": {
            "percentage": "10",
            "inclusive": False
        }
    })
    response = requests.request("POST", url, headers=headers, data=payload)

    return response.json()["id"]


def create_subscription(plan_id, return_url, cancel_url):
    url = "https://api-m.sandbox.paypal.com/v1/billing/subscriptions"
    payload = json.dumps({
        "plan_id": plan_id,
        "application_context": {
            "return_url": return_url,
            "cancel_url": cancel_url,
            "brand_name": "Your Brand Name",
            "locale": "en-US",
            "payment_method": {
                "payer_selected": "PAYPAL",
                "payee_preferred": "IMMEDIATE_PAYMENT_REQUIRED"
            }
        }
    })
    response = requests.post(url, headers=headers, data=payload)
    return response.json()['links'][0]['href'], response.json()['id']


def update_subscription(subscription_id, new_price):
    url = f"https://api-m.sandbox.paypal.com/v1/billing/subscriptions/{subscription_id}"
    payload = json.dumps([
        {
            "op": "replace",
            "path": "/plan/billing_cycles/@sequence==1/pricing_scheme/fixed_price",
            "value": {
                "currency_code": "USD",
                "value": f"{new_price}"
            }
        }
    ])
    response = requests.request("PATCH", url, headers=headers, data=payload)
    return response.text


def change_status_subscription(subscription_id, status="activate"):
    url = f"https://api-m.sandbox.paypal.com/v1/billing/subscriptions/{subscription_id}/{status}"

    payload = json.dumps({
        "reason": "Item out of stock"
    })
    response = requests.request("POST", url, headers=headers, data=payload)
    return response


def get_subscription_details(subscription_id):
    url = f"https://api-m.sandbox.paypal.com/v1/billing/subscriptions/{subscription_id}"
    payload = {}
    response = requests.request("GET", url, headers=headers, data=payload)
    return response


prod = create_product('teteasdtedtet', 'tetedasdtete')
plan_id = create_plan(prod, "dddddsaddd", "dddddasddd", 40)
subscription_link, subscription_id = create_subscription(plan_id, "https://google.com", "https://google.co")
# When return to frontend url -> GET params :
# https://www.google.com/?subscription_id=I-ML1EAUMB9TN3&ba_token=BA-44H338799N8339254&token=4CW62315494981215
# You can Use these params for your backend to save/check the payment
sub_details = get_subscription_details(subscription_id)
print(sub_details.json()['status'])
print(subscription_link)
# Check sub_detais['status'] == 'Active' to be sure sub is paid,
# there are also many different fiends in object to track the payments
update_subscription(subscription_id, 99)
change_status_subscription(subscription_id, "suspend")  # suspend the sub ||
# To test this you should put a breakpoint and proceed with payment
# (suspend/activate/cansel are statuses)
sub_details = get_subscription_details(subscription_id)
print(sub_details.json()['status'])


