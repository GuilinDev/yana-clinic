import sqlite3
import tempfile
from datetime import date, datetime, time
from io import StringIO
from pathlib import Path
from unittest import mock
from zoneinfo import ZoneInfo

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, TransactionTestCase, override_settings

from .models import Appointment
from .views import BOOKING_CLOSED_MESSAGE

CLINIC_TZ = ZoneInfo('America/New_York')


def clinic_now(*args):
    """Freeze 'now' at the given clinic-local time."""
    return mock.patch('django.utils.timezone.now', return_value=datetime(*args, tzinfo=CLINIC_TZ))


# Plain static storage so templates render without collectstatic's manifest
@override_settings(STORAGES={
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
})
class BookingCutoffTests(TestCase):
    # 2026-10-16 is a Friday, 10-17 a Saturday, 10-20 a Tuesday

    def available_times(self, date, location='wilmington'):
        response = self.client.get('/get-available-times/', {'date': date, 'location': location})
        return response.json()['available_times']

    def book(self, date, location='wilmington'):
        return self.client.post('/', {
            'your-name': 'Test', 'your-phone': '5550100', 'your-email': 'test@example.com',
            'your-service': 'Acupuncture', 'your-date': date, 'your-time': '10:00',
            'your-location': location,
        })

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
        self.assertFalse(Appointment.objects.exists())

    def test_post_rejects_day_location_is_closed(self):
        with clinic_now(2026, 10, 12, 9, 0):  # Monday
            response = self.book('2026-10-14')  # Wednesday is Chinatown only
        self.assertEqual(response.status_code, 400)
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
