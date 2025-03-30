import json
import requests
from django.conf import settings

class VivaWalletProcessor:
    def __init__(self):
        # Test Environment URL
        self.api_url = "https://demo.vivapayments.com/web/checkout"  # Test endpoint
        self.merchant_id = settings.VIVA_WALLET_MERCHANT_ID  # Add this to your settings
        self.api_key = settings.VIVA_WALLET_API_KEY  # Add this to your settings

    def process_payment(self, payment):
        # Prepare the payload for the request
        payload = {
            "amount": payment.amount * 100,  # Amount in cents
            "currencyCode": "978",  # Currency: EUR (978)
            "merchantTrns": str(payment.registration.id),
            "orderCode": str(payment.registration.id),
            "email": payment.registration.athletes.first().email,  # Take the first athlete's email for now
            "phone": payment.registration.athletes.first().phone,  # First athlete's phone
            "lang": "en",
            "paymentUrl": settings.VIVA_WALLET_PAYMENT_URL,  # Payment page URL (Test environment)
            "callbackUrl": settings.VIVA_WALLET_CALLBACK_URL,  # Callback URL after payment
            "returnUrl": settings.VIVA_WALLET_RETURN_URL,  # Return URL after successful payment
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # Sending the request to Viva Wallet Test Environment to get the payment link
        response = requests.post(self.api_url, data=json.dumps(payload), headers=headers)
        if response.status_code == 200:
            data = response.json()
            payment_url = data.get('paymentUrl')  # Extract the payment URL from the response
            return payment_url
        else:
            raise Exception("Error while processing payment with Viva Wallet Test Environment.")
