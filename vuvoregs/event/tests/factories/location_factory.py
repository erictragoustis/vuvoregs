import factory
from cities_light.models import Country, Region, City


class CountryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Country

    name = "Greece"
    code2 = "GR"


class RegionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Region

    name = "Attica"
    country = factory.SubFactory(CountryFactory)


class CityFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = City

    name = "Athens"
    region = factory.SubFactory(RegionFactory)
    country = factory.SelfAttribute("region.country")
