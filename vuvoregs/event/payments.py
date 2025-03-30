from payments import Payment
from payments.processor import BasePaymentProcessor

class VivaWalletProcessor(BasePaymentProcessor):
    def get_form_class(self):
        # Form class for your payment processor, typically a form for user input.
        return VivaWalletForm

    def get_transaction_data(self, payment):
        """
        Generate the transaction data required by the Viva Wallet API.
        """
        return {
            'amount': payment.amount,
            'currency': 'EUR',  # Assuming you are using Euros
            'description': f"Payment for Registration {payment.registration.id}",
            'callback_url': 'your-callback-url-here',
            # Add any other required params for Viva Wallet
        }

    def process_payment(self, payment):
        """
        Process the payment, typically by interacting with Viva Wallet API.
        """
        # Code to redirect user to Viva Wallet for payment here
        return 'Payment URL'  # Return URL for redirect

    def handle_notification(self, payment, notification):
        """
        Handle the notification from Viva Wallet after payment completion.
        This method will update the payment status in the database.
        """
        if notification.status == 'paid':
            payment.status = 'completed'
            payment.save()
            payment.registration.payment_status = 'paid'
            payment.registration.save()
        else:
            payment.status = 'failed'
            payment.save()
            payment.registration.payment_status = 'failed'
            payment.registration.save()