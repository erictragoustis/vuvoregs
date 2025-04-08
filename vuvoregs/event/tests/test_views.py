# event/tests/test_views.py

from django.test import TestCase
from django.urls import reverse
from event.models import Event, Package, PackageOption, Registration, Athlete

class ViewTests(TestCase):
    def setUp(self):
        self.event = Event.objects.create(name="Test Event", slug="test-event", distance=5)
        self.package = Package.objects.create(name="5K", event=self.event)
        self.option = PackageOption.objects.create(
            name="T-Shirt",
            options_json=["S", "M", "L"],
            options_string="S, M, L",
            package=self.package,
        )

    def test_register_view_valid(self):
        url = reverse("event:register", kwargs={"slug": self.event.slug})
        data = {
            "athlete-TOTAL_FORMS": "1",
            "athlete-INITIAL_FORMS": "0",
            "athlete-MIN_NUM_FORMS": "0",
            "athlete-MAX_NUM_FORMS": "1000",
            "athlete-0-first_name": "John",
            "athlete-0-last_name": "Doe",
            "athlete-0-email": "john@example.com",
            "athlete-0-package": self.package.id,
            f"athlete-0-option-{self.option.id}": "M",
            f"athlete-0-option-{self.option.id}-name": self.option.name,
        }
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Athlete.objects.filter(email="john@example.com").exists())

    def test_register_view_missing_required_option(self):
        url = reverse("event:register", kwargs={"slug": self.event.slug})
        data = {
            "athlete-TOTAL_FORMS": "1",
            "athlete-INITIAL_FORMS": "0",
            "athlete-MIN_NUM_FORMS": "0",
            "athlete-MAX_NUM_FORMS": "1000",
            "athlete-0-first_name": "John",
            "athlete-0-last_name": "Doe",
            "athlete-0-email": "john@example.com",
            "athlete-0-package": self.package.id,
            # Missing selected option intentionally
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This race requires at least 1 participants.")
