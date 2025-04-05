from django.test import TestCase, Client
from django.urls import reverse
from .forms import AthleteForm, athlete_formset_factory
from .models import Event, Race, RaceType, RacePackage, PackageOption, Athlete, Registration, PickUpPoint
from django.utils.timezone import now, timedelta

class ViewTests(TestCase):
    def setUp(self):
        self.event = Event.objects.create(
            name="Test Event",
            date=now().date() + timedelta(days=5),
            location="City",
            is_available=True,
            registration_start_date=now() - timedelta(days=1),
            registration_end_date=now() + timedelta(days=3)
        )

        self.race_type = RaceType.objects.create(name="5K")
        self.race = Race.objects.create(
            event=self.event,
            race_type=self.race_type,
            race_km=5.0,
            min_participants=1
        )

        self.package = RacePackage.objects.create(
            event=self.event,
            name="Standard",
            description="Standard package",
            price=20.00
        )
        self.package.races.add(self.race)

        self.pickup_point = PickUpPoint.objects.create(
            event=self.event,
            name="Main Booth",
            address="123 Street",
            working_hours="9am–5pm"
        )

        self.registration = Registration.objects.create(event=self.event)

    def test_event_list_view(self):
        url = reverse('event_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Event")

    def test_race_list_view_valid(self):
        url = reverse('race_list', args=[self.event.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "5K")

    def test_race_list_view_invalid(self):
        url = reverse('race_list', args=[9999])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Registrations are closed")

    def test_registration_view_get(self):
        url = reverse('registration', args=[self.race.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Register for")

    def test_package_options_valid(self):
        PackageOption.objects.create(package=self.package, name="Size", options_json=["S", "M", "L"])
        url = reverse('package_options', args=[self.package.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("package_options", response.json())

    def test_package_options_invalid(self):
        url = reverse('package_options', args=[9999])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"package_options": []})

    def test_payment_view(self):
        url = reverse('payment', args=[self.registration.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Payment")

    def test_payment_success_view(self):
        url = reverse('payment_success', args=[self.registration.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "success")

    def test_payment_failure_view(self):
        url = reverse('payment_failure', args=[self.registration.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Payment Failed")
    
    def test_registration_closed_redirects_to_closed_template(self):
        self.event.registration_end_date = now() - timedelta(days=1)
        self.event.save()

        url = reverse('registration', args=[self.race.id])
        response = self.client.get(url)
        self.assertTemplateUsed(response, 'registration/closed.html')
        
    def test_payment_view_post_success(self):
        url = reverse('payment', args=[self.registration.id])
        response = self.client.post(url)
        self.registration.refresh_from_db()
        self.assertEqual(self.registration.status, 'completed')
        self.assertRedirects(response, reverse('payment_success', args=[self.registration.id]))

    def test_payment_view_post_failure(self):
        url = reverse('payment', args=[self.registration.id])
        response = self.client.post(url, data={"mock_fail": "1"})
        self.registration.refresh_from_db()
        self.assertEqual(self.registration.status, 'failed')
        self.assertRedirects(response, reverse('payment_failure', args=[self.registration.id]))


    def test_registration_view_post_creates_registration_and_athletes(self):
        from .forms import athlete_formset_factory
        from .models import Athlete

        # Create a PackageOption for dynamic JS fields
        option = PackageOption.objects.create(
            package=self.package,
            name="T-Shirt",
            options_json=["S", "M", "L"]
        )

        url = reverse('registration', args=[self.race.id])

        post_data = {
            # Formset management data
            'athletes-TOTAL_FORMS': '2',
            'athletes-INITIAL_FORMS': '0',
            'athletes-MIN_NUM_FORMS': '0',
            'athletes-MAX_NUM_FORMS': '1000',

            # Athlete 0
            'athletes-0-first_name': 'Lara',
            'athletes-0-last_name': 'Croft',
            'athletes-0-email': 'lara@example.com',
            'athletes-0-phone': '1234567890',
            'athletes-0-sex': 'Female',
            'athletes-0-dob': '1985-02-14',
            'athletes-0-hometown': 'Tomb Raider HQ',
            'athletes-0-package': str(self.package.id),
            'athletes-0-pickup_point': str(self.pickup_point.id),
            'athlete-0-option-1': 'M',
            'athlete-0-option-1-name': 'T-Shirt',

            # Athlete 1
            'athletes-1-first_name': 'Nathan',
            'athletes-1-last_name': 'Drake',
            'athletes-1-email': 'nathan@example.com',
            'athletes-1-phone': '9876543210',
            'athletes-1-sex': 'Male',
            'athletes-1-dob': '1983-06-15',
            'athletes-1-hometown': 'Adventure Town',
            'athletes-1-package': str(self.package.id),
            'athletes-1-pickup_point': str(self.pickup_point.id),
            'athlete-1-option-1': 'L',
            'athlete-1-option-1-name': 'T-Shirt',
        }

        # Submit the POST
        response = self.client.post(url, data=post_data)

        # Follow redirect to /payment/<id>/
        self.assertEqual(response.status_code, 302)
        registration_id = response.url.split('/')[-2]
        registration = Registration.objects.get(pk=registration_id)

        # Ensure registration has 2 athletes
        athletes = registration.athletes.order_by('first_name')
        self.assertEqual(athletes.count(), 2)
        self.assertEqual(athletes[0].first_name, "Lara")
        self.assertEqual(athletes[1].first_name, "Nathan")

        self.assertEqual(athletes[0].selected_options, {"T-Shirt": ["M"]})
        self.assertEqual(athletes[1].selected_options, {"T-Shirt": ["L"]})

    def test_registration_total_amount_and_payment_view_reflects_total(self):
        from .models import Registration

        # Create multiple packages with different prices (if needed)
        self.package.price = 25.00
        self.package.save()

        # Create a PackageOption to simulate frontend JS selections
        PackageOption.objects.create(
            package=self.package,
            name="T-Shirt",
            options_json=["S", "M", "L"]
        )

        url = reverse('registration', args=[self.race.id])

        post_data = {
            # Formset management
            'athletes-TOTAL_FORMS': '2',
            'athletes-INITIAL_FORMS': '0',
            'athletes-MIN_NUM_FORMS': '0',
            'athletes-MAX_NUM_FORMS': '1000',

            # Athlete 0
            'athletes-0-first_name': 'Lara',
            'athletes-0-last_name': 'Croft',
            'athletes-0-email': 'lara@example.com',
            'athletes-0-phone': '1234567890',
            'athletes-0-sex': 'Female',
            'athletes-0-dob': '1985-02-14',
            'athletes-0-hometown': 'Tomb Raider HQ',
            'athletes-0-package': str(self.package.id),
            'athletes-0-pickup_point': str(self.pickup_point.id),
            'athlete-0-option-1': 'M',
            'athlete-0-option-1-name': 'T-Shirt',

            # Athlete 1
            'athletes-1-first_name': 'Nathan',
            'athletes-1-last_name': 'Drake',
            'athletes-1-email': 'nathan@example.com',
            'athletes-1-phone': '9876543210',
            'athletes-1-sex': 'Male',
            'athletes-1-dob': '1983-06-15',
            'athletes-1-hometown': 'Adventure Town',
            'athletes-1-package': str(self.package.id),
            'athletes-1-pickup_point': str(self.pickup_point.id),
            'athlete-1-option-1': 'L',
            'athlete-1-option-1-name': 'T-Shirt',
        }

        # Submit the form
        response = self.client.post(url, data=post_data)

        # Assert redirect to /payment/<registration_id>/
        self.assertEqual(response.status_code, 302)
        registration_id = response.url.split("/")[-2]
        registration = Registration.objects.get(pk=registration_id)

        # ✅ 2 athletes × $25 = $50 total
        self.assertEqual(float(registration.total_amount), 50.00)

        # ✅ Check that payment view shows this total
        payment_url = reverse('payment', args=[registration.id])
        payment_response = self.client.get(payment_url)
        self.assertEqual(payment_response.status_code, 200)
        self.assertContains(payment_response, "$50.00")


class RegistrationTestCase(TestCase):
    """
    Tests the registration form submission with:
    - Valid athlete info
    - Valid package and pickup point
    - Dynamic package option saving
    """
    def setUp(self):
        # ✅ Create an event open for registration
        self.event = Event.objects.create(
            name="Test Event",
            date=now().date() + timedelta(days=10),
            location="Test Location",
            is_available=True,
            registration_start_date=now() - timedelta(days=1),
            registration_end_date=now() + timedelta(days=5),
        )

        # ✅ Add a pickup point
        self.pickup_point = PickUpPoint.objects.create(
            event=self.event,
            name="Central Depot",
            address="123 Pickup Lane",
            working_hours="9am–5pm"
        )

        # ✅ Race & RaceType
        self.race_type = RaceType.objects.create(name="10K")
        self.race = Race.objects.create(
            event=self.event,
            race_type=self.race_type,
            race_km=10.0,
            min_participants=1
        )

        # ✅ Package
        self.package = RacePackage.objects.create(
            event=self.event,
            name="Standard",
            description="Standard package",
            price=25.00
        )
        self.package.races.add(self.race)

        # ✅ Package option
        self.option = PackageOption.objects.create(
            package=self.package,
            name="T-Shirt"
        )
        self.option.set_options_from_string("S,M,L,XL")

        self.client = Client()

    def test_registration_creates_athlete_and_redirects_to_payment(self):
        """
        Posts valid athlete data via formset and expects:
        - One registration and athlete created
        - Total calculated
        - JSON option saved
        - Redirect to payment page
        """
        url = reverse('registration', args=[self.race.id])

        post_data = {
            # ✅ Formset management keys
            'athletes-TOTAL_FORMS': '1',
            'athletes-INITIAL_FORMS': '0',
            'athletes-MIN_NUM_FORMS': '0',
            'athletes-MAX_NUM_FORMS': '1000',

            # ✅ Athlete form fields (prefix: athletes-0-)
            'athletes-0-first_name': 'Alice',
            'athletes-0-last_name': 'Smith',
            'athletes-0-email': 'alice@example.com',
            'athletes-0-phone': '1234567890',
            'athletes-0-sex': 'Female',
            'athletes-0-dob': '1990-01-01',
            'athletes-0-hometown': 'Testville',
            'athletes-0-package': str(self.package.id),
            'athletes-0-pickup_point': str(self.pickup_point.id),

            # ✅ Dynamic JS fields for package options
            f'athlete-0-option-{self.option.id}': 'M',
            f'athlete-0-option-{self.option.id}-name': self.option.name,
        }

        # Submit the POST request
        response = self.client.post(url, post_data)

        # ✅ Check that it redirects to payment
        self.assertEqual(response.status_code, 302)

        # ✅ Get the newly created registration
        registration = Registration.objects.latest('created_at')
        self.assertEqual(registration.total_amount, self.package.price)

        # ✅ Get the athlete
        athlete = registration.athletes.first()
        self.assertIsNotNone(athlete)
        self.assertEqual(athlete.first_name, 'Alice')
        self.assertEqual(athlete.pickup_point, self.pickup_point)
        self.assertIn("T-Shirt", athlete.selected_options)
        self.assertIn("M", athlete.selected_options["T-Shirt"])

class AjaxPackageOptionTestCase(TestCase):
    def setUp(self):
        # Minimal setup for a package and option
        self.event = Event.objects.create(
            name="Ajax Test Event",
            date=now().date() + timedelta(days=5),
            location="Testville",
            is_available=True,
            registration_start_date=now() - timedelta(days=1),
            registration_end_date=now() + timedelta(days=3)
        )

        self.race_type = RaceType.objects.create(name="5K")
        self.race = Race.objects.create(
            event=self.event,
            race_type=self.race_type,
            race_km=5.0
        )

        self.package = RacePackage.objects.create(
            event=self.event,
            name="Basic",
            description="Basic Package",
            price=20.00
        )
        self.package.races.add(self.race)

        self.option = PackageOption.objects.create(
            package=self.package,
            name="Color"
        )
        self.option.set_options_from_string("Red, Blue, Green")

    def test_valid_package_returns_options(self):
        url = reverse('package_options', args=[self.package.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('package_options', data)
        self.assertEqual(len(data['package_options']), 1)
        self.assertEqual(data['package_options'][0]['name'], 'Color')
        self.assertIn('options_json', data['package_options'][0])
        self.assertIn('Red', data['package_options'][0]['options_json'])

    def test_invalid_package_returns_empty(self):
        url = reverse('package_options', args=[9999])  # Non-existent package ID
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data, {'package_options': []})
        
def test_package_with_no_options_returns_empty(self):
    empty_package = RacePackage.objects.create(
        event=self.event,
        name="Empty",
        description="No options here",
        price=10.0
    )
    empty_package.races.add(self.race)

    url = reverse('package_options', args=[empty_package.id])
    response = self.client.get(url)

    self.assertEqual(response.status_code, 200)
    data = response.json()
    self.assertEqual(data['package_options'], [])
    
class AthleteFormTestCase(TestCase):
    def setUp(self):
        # 🎯 Create a test event
        self.event = Event.objects.create(
            name="Test Event",
            date=now().date() + timedelta(days=10),
            location="City",
            is_available=True,
            registration_start_date=now() - timedelta(days=2),
            registration_end_date=now() + timedelta(days=5)
        )

        # 🏁 Race and type
        self.race_type = RaceType.objects.create(name="Half Marathon")
        self.race = Race.objects.create(
            name="Half",
            event=self.event,
            race_type=self.race_type,
            race_km=21.1,
            min_participants=1
        )

        # 📦 Package
        self.package = RacePackage.objects.create(
            event=self.event,
            name="Elite Package",
            description="Elite runners only",
            price=50.00
        )
        self.package.races.add(self.race)

        # 📍 Pickup point
        self.pickup_point = PickUpPoint.objects.create(
            event=self.event,
            name="Expo Booth",
            address="123 Main St",
            working_hours="9am–6pm"
        )

    def test_valid_form_passes(self):
        form = AthleteForm(data={
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john@example.com',
            'phone': '1234567890',
            'sex': 'Male',
            'dob': '1990-01-01',
            'hometown': 'RunnerTown',
            'package': self.package.id,
            'pickup_point': self.pickup_point.id,
        }, race=self.race, packages=RacePackage.objects.filter(event=self.event))

        self.assertTrue(form.is_valid())
        athlete = form.save(commit=False)
        self.assertEqual(athlete.package, self.package)
        self.assertEqual(athlete.pickup_point, self.pickup_point)

    def test_missing_required_field_fails(self):
        form = AthleteForm(data={
            'first_name': '',  # Missing on purpose
            'last_name': 'Doe',
            'email': 'john@example.com',
            'phone': '1234567890',
            'sex': 'Male',
            'dob': '1990-01-01',
            'hometown': 'RunnerTown',
            'package': self.package.id,
            'pickup_point': self.pickup_point.id,
        }, race=self.race, packages=RacePackage.objects.filter(event=self.event))

        self.assertFalse(form.is_valid())
        self.assertIn('first_name', form.errors)

    def test_pickup_point_not_in_event_is_filtered_out(self):
        wrong_event = Event.objects.create(
            name="Other Event",
            date=now().date() + timedelta(days=30),
            location="Other City"
        )
        wrong_pickup = PickUpPoint.objects.create(
            event=wrong_event,
            name="Wrong Location",
            address="Nowhere",
            working_hours="Never"
        )

        form = AthleteForm(data={
            'first_name': 'Anna',
            'last_name': 'Smith',
            'email': 'anna@example.com',
            'phone': '9876543210',
            'sex': 'Female',
            'dob': '1995-05-05',
            'hometown': 'Runville',
            'package': self.package.id,
            'pickup_point': wrong_pickup.id,  # ❌ Wrong event
        }, race=self.race, packages=RacePackage.objects.filter(event=self.event))

        self.assertFalse(form.is_valid())
        self.assertIn('pickup_point', form.errors)

    def test_package_queryset_is_filtered(self):
        # This simulates a custom filtered (empty) package list
        form = AthleteForm(
            data={},  # Required to trigger field init
            race=self.race,
            packages=RacePackage.objects.none()
        )
        self.assertEqual(list(form.fields['package'].queryset), [])
        
    def test_selected_options_saved_as_json(self):
        from .models import Registration

        registration = Registration.objects.create(
            event=self.event,
            total_amount=0,
            payment_status='not_paid',
            status='pending'
        )

        selected_options = {
            "T-Shirt": ["M"],
            "Medal": ["Gold"]
        }

        form = AthleteForm(data={
            'first_name': 'Lara',
            'last_name': 'Croft',
            'email': 'lara@example.com',
            'phone': '1234567890',
            'sex': 'Female',
            'dob': '1985-02-14',
            'hometown': 'Tomb Raider HQ',
            'package': self.package.id,
            'pickup_point': self.pickup_point.id
        }, race=self.race, packages=RacePackage.objects.filter(event=self.event))

        self.assertTrue(form.is_valid(), form.errors)
        athlete = form.save(commit=False)
        athlete.race = self.race
        athlete.registration = registration

        # ✅ manually set JS-style data
        athlete.selected_options = selected_options
        athlete.save()

        self.assertIsInstance(athlete.selected_options, dict)
        self.assertEqual(athlete.selected_options["T-Shirt"], ["M"])
        self.assertEqual(athlete.selected_options["Medal"], ["Gold"])

    def test_selected_options_extracted_from_dynamic_js_fields(self):
        from .models import Registration

        registration = Registration.objects.create(
            event=self.event,
            total_amount=0,
            payment_status='not_paid',
            status='pending'
        )

        # Simulate dynamic JS fields like athlete-0-option-1
        dynamic_post = {
            'athlete-0-option-1': ['M'],
            'athlete-0-option-1-name': 'T-Shirt'
        }

        # Normal athlete form fields (formset-style: prefix = 'athletes')
        form_data = {
            'athletes-TOTAL_FORMS': '1',
            'athletes-INITIAL_FORMS': '0',
            'athletes-MIN_NUM_FORMS': '0',
            'athletes-MAX_NUM_FORMS': '1000',
            'athletes-0-first_name': 'Lara',
            'athletes-0-last_name': 'Croft',
            'athletes-0-email': 'lara@example.com',
            'athletes-0-phone': '1234567890',
            'athletes-0-sex': 'Female',
            'athletes-0-dob': '1985-02-14',
            'athletes-0-hometown': 'Tomb Raider HQ',
            'athletes-0-package': self.package.id,
            'athletes-0-pickup_point': self.pickup_point.id,
        }

        # Merge form and dynamic data
        post_data = {**form_data, **dynamic_post}

        # Build the form manually (simulating formset[0])
        athlete_form = AthleteForm(
            data={key.replace('athletes-0-', ''): val for key, val in form_data.items() if key.startswith('athletes-0-')},
            race=self.race,
            packages=RacePackage.objects.filter(event=self.event)
        )

        self.assertTrue(athlete_form.is_valid(), athlete_form.errors)
        athlete = athlete_form.save(commit=False)
        athlete.race = self.race
        athlete.registration = registration

        # ✅ Simulate JS-style option parsing like your view does
        selected_options = {}
        index = 0
        for key, value in post_data.items():
            if key.startswith(f'athlete-{index}-option-') and not key.endswith('-name'):
                option_id = key.split(f'athlete-{index}-option-')[-1]
                name_key = f'{key}-name'
                option_name = post_data.get(name_key, f'Option {option_id}')
                selected_options[option_name] = value if isinstance(value, list) else [value]

        athlete.selected_options = selected_options
        athlete.save()

        self.assertEqual(athlete.selected_options, {"T-Shirt": ["M"]})
        
    def test_multiple_athletes_with_selected_options(self):
        from .models import Registration

        registration = Registration.objects.create(
            event=self.event,
            total_amount=0,
            payment_status='not_paid',
            status='pending'
        )

        post_data = {
            # Formset management
            'athletes-TOTAL_FORMS': '2',
            'athletes-INITIAL_FORMS': '0',
            'athletes-MIN_NUM_FORMS': '0',
            'athletes-MAX_NUM_FORMS': '1000',

            # Athlete 0
            'athletes-0-first_name': 'Lara',
            'athletes-0-last_name': 'Croft',
            'athletes-0-email': 'lara@example.com',
            'athletes-0-phone': '1234567890',
            'athletes-0-sex': 'Female',
            'athletes-0-dob': '1985-02-14',
            'athletes-0-hometown': 'Tomb Raider HQ',
            'athletes-0-package': self.package.id,
            'athletes-0-pickup_point': self.pickup_point.id,

            'athlete-0-option-1': 'M',
            'athlete-0-option-1-name': 'T-Shirt',

            # Athlete 1
            'athletes-1-first_name': 'Nathan',
            'athletes-1-last_name': 'Drake',
            'athletes-1-email': 'nathan@example.com',
            'athletes-1-phone': '9876543210',
            'athletes-1-sex': 'Male',
            'athletes-1-dob': '1983-06-15',
            'athletes-1-hometown': 'Adventure Town',
            'athletes-1-package': self.package.id,
            'athletes-1-pickup_point': self.pickup_point.id,

            'athlete-1-option-1': 'L',
            'athlete-1-option-1-name': 'T-Shirt',
        }

        # Create the formset
        AthleteFormSet = athlete_formset_factory(self.race)
        formset = AthleteFormSet(
            data=post_data,
            form_kwargs={
                'race': self.race,
                'packages': RacePackage.objects.filter(event=self.event)
            }
        )

        self.assertTrue(formset.is_valid(), formset.errors)

        for i, form in enumerate(formset.forms):
            athlete = form.save(commit=False)
            athlete.race = self.race
            athlete.registration = registration

            # Extract selected options for each athlete using simulated JS logic
            selected_options = {}
            for key, value in post_data.items():
                if key.startswith(f'athlete-{i}-option-') and not key.endswith('-name'):
                    option_id = key.split(f'athlete-{i}-option-')[-1]
                    name_key = f'{key}-name'
                    option_name = post_data.get(name_key, f'Option {option_id}')
                    selected_options[option_name] = value if isinstance(value, list) else [value]

            athlete.selected_options = selected_options
            athlete.save()

        # Validate what got saved
        athletes = registration.athletes.order_by('first_name')
        self.assertEqual(len(athletes), 2)
        self.assertEqual(athletes[0].first_name, 'Lara')
        self.assertEqual(athletes[0].selected_options, {'T-Shirt': ['M']})
        self.assertEqual(athletes[1].first_name, 'Nathan')
        self.assertEqual(athletes[1].selected_options, {'T-Shirt': ['L']})


