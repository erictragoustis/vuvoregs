from django.http import HttpResponse
from django.urls import reverse
import requests

from payments import PaymentStatus, RedirectNeeded
from payments.core import BasicProvider


class VivaSmartCheckoutProvider(BasicProvider):
    """Viva Wallet Smart Checkout provider for django-payments (correct full flow)."""

    def __init__(
        self,
        merchant_id,
        api_key,
        client_id,
        client_secret,
        source_code,
        sandbox=True,
        **kwargs,
    ):
        self.merchant_id = merchant_id
        self.api_key = api_key
        self.client_id = client_id
        self.client_secret = client_secret
        self.source_code = source_code
        self.sandbox = sandbox
        self.base_url = (
            "https://demo-accounts.vivapayments.com"
            if sandbox
            else "https://accounts.vivapayments.com"
        )
        self.checkout_base_url = (
            "https://demo.vivapayments.com/web/checkout"
            if sandbox
            else "https://www.vivapayments.com/web/checkout"
        )
        super().__init__(**kwargs)

    def get_token(self):
        """
        Step 1: Authenticate via OAuth2 to get access token.
        """
        url = f"{self.base_url}/connect/token"
        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        response = requests.post(url, data=data, headers=headers)
        response.raise_for_status()
        return response.json()["access_token"]

    def create_order(self, payment):
        """Step 2: Create the payment order and get orderCode."""
        token = self.get_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        amount_in_cents = int(payment.total * 100)
        data = {
            "amount": amount_in_cents,
            "customerTrns": f"Registration {payment.id}",
            "customer": {
                "email": payment.billing_email,
                "phone": str(payment.billing_phone) if payment.billing_phone else "",
                "fullName": f"{payment.billing_first_name} {payment.billing_last_name}",
            },
            "paymentTimeout": 300,
            "preauth": False,
            "sourceCode": self.source_code,
            "merchantTrns": f"reg-{payment.id}",
        }

        url = (
            "https://demo-api.vivapayments.com/checkout/v2/orders"
            if self.sandbox
            else "https://api.vivapayments.com/checkout/v2/orders"
        )
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        print("📦 Viva order response:", response.json())  # ✅ Add this here
        return response.json()["orderCode"]

    def get_redirect_url(self, payment):
        """Step 3: Build redirect URL to Viva Smart Checkout."""
        order_code = self.create_order(payment)
        print("💡 Saving order_code:", order_code)

        # ✅ Save only order_code here — transaction_id comes from webhook/redirect
        payment.order_code = str(order_code)
        payment.save(update_fields=["order_code"])
        payment.change_status(PaymentStatus.WAITING)

        return f"{self.checkout_base_url}?ref={order_code}"

    def get_form(self, payment, data=None):
        """Called by django-payments. Immediately redirects to Smart Checkout."""
        redirect_url = self.get_redirect_url(payment)
        raise RedirectNeeded(redirect_url)

    def process_data(self, payment, request):
        """Called by django-payments when user returns to /payments/process/<uuid>/.

        For Smart Checkout, we handle everything via success/failure URLs, so this is a no-op.
        """
        return HttpResponse("OK")
