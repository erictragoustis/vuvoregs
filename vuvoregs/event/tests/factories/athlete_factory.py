import factory
from event.models import Athlete
from .registration_factory import RegistrationFactory
from .race_factory import RaceFactory
from .race_package_factory import RacePackageFactory


class AthleteFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Athlete

    registration = factory.SubFactory(RegistrationFactory)
    race = factory.SubFactory(RaceFactory)
    package = factory.SubFactory(RacePackageFactory)
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    email = factory.Faker("email")
    phone = factory.Faker("phone_number")
    dob = factory.Faker("date_of_birth")
