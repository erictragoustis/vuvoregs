import factory
from event.models import Payment
from event.models.registration import Registration


class PaymentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Payment
        skip_postgeneration_save = True  # ✅ suppress factory_boy warning

    variant = "viva"
    currency = "EUR"
    status = "waiting"
    total = 0
    transaction_id = factory.Sequence(lambda n: f"TX{n:05d}")
    order_code = factory.Sequence(lambda n: f"ORD{n:05d}")

    # custom logic to associate with registration
    @factory.post_generation
    def set_registration(payment, create, extracted, **kwargs):
        if extracted:
            payment.registration = extracted
            payment.extra_data = factory.LazyFunction(
                lambda: f'{{"registration_id": {extracted.id}}}'
            )
            payment.save()
