import sqlite3
import tempfile
from datetime import date, datetime, time
from io import StringIO
from pathlib import Path
from unittest import mock
from zoneinfo import ZoneInfo

from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, TransactionTestCase, override_settings

from .booking import BOOKING_CLOSED_MESSAGE, SLOT_TAKEN_MESSAGE
from .models import Appointment
from .views import BOOKING_RATE_LIMIT

CLINIC_TZ = ZoneInfo('America/New_York')


def clinic_now(*args):
    """Freeze 'now' at the given clinic-local time."""
    return mock.patch('django.utils.timezone.now', return_value=datetime(*args, tzinfo=CLINIC_TZ))


# Plain static storage so templates render without collectstatic's manifest
PLAIN_STATIC = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
}

VALID_BOOKING = {
    'your-name': 'Test Patient', 'your-phone': '978-555-0100', 'your-email': 'test@example.com',
    'your-service': 'Acupuncture/Prescription Chinese medicine', 'your-date': '2026-10-17',
    'your-time': '10:00', 'your-location': 'wilmington', 'your-message': '',
}


@override_settings(STORAGES=PLAIN_STATIC)
class BookingCutoffTests(TestCase):
    # 2026-10-16 is a Friday, 10-17 a Saturday, 10-20 a Tuesday

    def available_times(self, date, location='wilmington'):
        response = self.client.get('/get-available-times/', {'date': date, 'location': location})
        return response.json()['available_times']

    def book(self, date, location='wilmington'):
        return self.client.post('/', {**VALID_BOOKING, 'your-date': date, 'your-location': location})

    def test_same_day_is_closed(self):
        with clinic_now(2026, 10, 17, 9, 0):  # Saturday morning
            self.assertEqual(self.available_times('2026-10-17'), [])
            self.assertTrue(self.available_times('2026-10-20'))

    def test_next_day_open_before_cutoff(self):
        with clinic_now(2026, 10, 16, 17, 59):  # Friday
            self.assertTrue(self.available_times('2026-10-17'))

    def test_next_day_closed_from_cutoff(self):
        with clinic_now(2026, 10, 16, 18, 0):  # Friday
            self.assertEqual(self.available_times('2026-10-17'), [])
            self.assertTrue(self.available_times('2026-10-20'))

    def test_post_rejects_closed_date(self):
        with clinic_now(2026, 10, 16, 18, 0):
            response = self.book('2026-10-17')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['error'], BOOKING_CLOSED_MESSAGE)
        self.assertEqual(response.json()['errors'], {'your-date': [BOOKING_CLOSED_MESSAGE]})
        self.assertFalse(Appointment.objects.exists())

    def test_post_rejects_day_location_is_closed(self):
        with clinic_now(2026, 10, 12, 9, 0):  # Monday
            response = self.book('2026-10-14')  # Wednesday is Chinatown only
        self.assertEqual(response.status_code, 400)
        self.assertIn('your-date', response.json()['errors'])
        self.assertFalse(Appointment.objects.exists())

    def test_post_accepts_open_date(self):
        with clinic_now(2026, 10, 16, 17, 59):
            response = self.book('2026-10-17')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Appointment.objects.count(), 1)

    def test_home_shows_min_date_and_notice(self):
        with clinic_now(2026, 10, 16, 18, 0):
            response = self.client.get('/')
        self.assertContains(response, 'min="2026-10-18"')
        self.assertContains(response, 'Please book online by 6:00 PM the day before your visit.')
        self.assertContains(response, 'href="sms:+19787295878"')

    def test_head_requests_work_for_uptime_monitors(self):
        self.assertEqual(self.client.head('/').status_code, 200)
        self.assertEqual(self.client.head('/get-available-times/?date=2026-10-20').status_code, 200)
        self.assertEqual(self.client.put('/').status_code, 405)


@override_settings(STORAGES=PLAIN_STATIC)
class BookingFormTests(TestCase):
    def setUp(self):
        cache.clear()
        self.now = clinic_now(2026, 10, 16, 9, 0)  # Friday morning; Saturday 10-17 is bookable
        self.now.start()
        self.addCleanup(self.now.stop)

    def post(self, **overrides):
        data = {**VALID_BOOKING, **overrides}
        for key, value in overrides.items():
            if value is None:
                del data[key]
        return self.client.post('/', data)

    def test_success_returns_booking_details(self):
        response = self.post()
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload['ok'])
        self.assertEqual(payload['appointment']['date_display'], 'Saturday, October 17, 2026')
        self.assertEqual(payload['appointment']['time_display'], '10:00 AM')
        self.assertEqual(payload['appointment']['location_name'], 'Wilmington')
        self.assertEqual(payload['appointment']['phone_link'], '+19787295878')
        appointment = Appointment.objects.get()
        self.assertEqual(appointment.phone, '(978) 555-0100')
        self.assertEqual(appointment.status, Appointment.STATUS_PENDING)
        self.assertIsNotNone(appointment.created_at)

    def test_missing_fields_are_reported_per_field(self):
        response = self.post(**{'your-name': None, 'your-email': 'not-an-email'})
        self.assertEqual(response.status_code, 400)
        errors = response.json()['errors']
        self.assertEqual(errors['your-name'], ['Please enter your name.'])
        self.assertEqual(errors['your-email'], ['Please enter a valid email address.'])
        self.assertFalse(Appointment.objects.exists())

    def test_phone_must_look_like_a_phone_number(self):
        response = self.post(**{'your-phone': '12345'})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['errors'], {'your-phone': ['Please enter a valid phone number.']})

    def test_time_must_be_an_open_slot(self):
        response = self.post(**{'your-time': '08:15'})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['errors'], {'your-time': ['Please choose a time from the list.']})

    def test_honeypot_submission_is_ignored_but_looks_successful(self):
        response = self.post(**{'your-website': 'http://spam.example'})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['ok'])
        self.assertFalse(Appointment.objects.exists())

    def test_slot_cannot_be_double_booked(self):
        self.assertEqual(self.post().status_code, 200)
        response = self.post(**{'your-name': 'Second Patient', 'your-email': 'second@example.com'})
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()['errors'], {'your-time': [SLOT_TAKEN_MESSAGE]})
        self.assertEqual(Appointment.objects.count(), 1)
        # Another location or a cancelled booking does not block the slot
        self.assertEqual(self.post(**{'your-date': '2026-10-19', 'your-location': 'chinatown'}).status_code, 200)
        Appointment.objects.filter(location='wilmington').update(status=Appointment.STATUS_CANCELLED)
        self.assertEqual(self.post(**{'your-name': 'Third Patient'}).status_code, 200)

    def test_available_times_exclude_booked_slots(self):
        self.post()
        response = self.client.get('/get-available-times/', {'date': '2026-10-17', 'location': 'wilmington'})
        times = response.json()['available_times']
        self.assertNotIn('10:00', times)
        self.assertIn('10:30', times)
        self.assertEqual(times[0], '09:00')
        self.assertEqual(times[-1], '17:30')

    def test_rate_limit_applies_per_public_client_address(self):
        # (The documentation ranges 203.0.113.0/24 etc. count as private to ipaddress, so use real public IPs)
        headers = {'HTTP_X_FORWARDED_FOR': '8.8.8.8'}
        for _ in range(BOOKING_RATE_LIMIT):
            response = self.client.post('/', {'your-name': 'x'}, **headers)
            self.assertEqual(response.status_code, 400)
        response = self.client.post('/', {'your-name': 'x'}, **headers)
        self.assertEqual(response.status_code, 429)
        # A different client is unaffected; only the last (proxy-appended) address counts
        response = self.client.post('/', {'your-name': 'x'}, HTTP_X_FORWARDED_FOR='8.8.8.8, 1.1.1.1')
        self.assertEqual(response.status_code, 400)

    def test_rate_limit_is_skipped_when_the_client_cannot_be_identified(self):
        # Requests arriving from the reverse proxy without X-Forwarded-For share 127.0.0.1
        for _ in range(BOOKING_RATE_LIMIT + 1):
            response = self.client.post('/', {'your-name': 'x'})
            self.assertEqual(response.status_code, 400)


@override_settings(STORAGES=PLAIN_STATIC)
class AdminTests(TestCase):
    def setUp(self):
        self.client.force_login(User.objects.create_superuser('admin', 'admin@example.com', 'pw'))
        self.appointment = Appointment.objects.create(
            name='Export Me', phone='(978) 555-0100', email='export@example.com',
            service='Acupuncture', date=date(2026, 11, 3), time=time(10, 0), location='wilmington',
        )

    def test_changelist_and_csv_export(self):
        self.assertEqual(self.client.get('/yana/website/appointment/').status_code, 200)
        response = self.client.post('/yana/website/appointment/', {
            'action': 'export_csv', '_selected_action': [self.appointment.pk],
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv; charset=utf-8')
        body = response.content.decode()
        self.assertIn('Export Me', body)
        self.assertIn('Pending', body)

    def test_mark_confirmed_action(self):
        self.client.post('/yana/website/appointment/', {
            'action': 'mark_confirmed', '_selected_action': [self.appointment.pk],
        })
        self.appointment.refresh_from_db()
        self.assertEqual(self.appointment.status, Appointment.STATUS_CONFIRMED)


# TransactionTestCase: the SQLite backup API cannot copy while this connection
# holds the open transaction that TestCase wraps around every test.
class BackupDbTests(TransactionTestCase):
    def test_backup_is_a_readable_copy_and_old_backups_are_pruned(self):
        Appointment.objects.create(
            name='Backup Test', phone='5550100', email='backup@example.com',
            date=date(2026, 11, 3), time=time(10, 0), location='wilmington',
        )
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp)
            for day in ('01', '02', '03'):  # older backups that should be pruned
                (dest / f'db-2026-01-{day}-000000.sqlite3').write_bytes(b'')

            out = StringIO()
            call_command('backup_db', dest=tmp, keep=2, stdout=out)

            backups = sorted(dest.glob('db-*.sqlite3'))
            self.assertEqual(len(backups), 2)
            self.assertEqual(backups[0].name, 'db-2026-01-03-000000.sqlite3')
            self.assertIn('2 backup(s) kept', out.getvalue())

            copy = sqlite3.connect(str(backups[-1]))
            try:
                rows = copy.execute('select name from website_appointment').fetchall()
            finally:
                copy.close()
            self.assertEqual(rows, [('Backup Test',)])

    def test_keep_must_be_positive(self):
        with tempfile.TemporaryDirectory() as tmp, self.assertRaises(CommandError):
            call_command('backup_db', dest=tmp, keep=0)
