"""Booking rules shared by the views, the form and the templates.

Everything about when the clinic can be booked online lives here, in one place.
"""
from datetime import time, timedelta

from django.utils import timezone

LOCATIONS = {
    'wilmington': {
        'name': 'Wilmington',
        'address': '420 Main Street, Wilmington, MA 01887',
        'phone': '(978) 729-5878',
        'phone_link': '+19787295878',
    },
    'chinatown': {
        'name': 'Chinatown (Boston)',
        'address': '65 Harrison Ave. Suite 201B, Boston, MA 02111',
        'phone': '(617) 451-7500',
        'phone_link': '+16174517500',
    },
}

# Open days per location (Python weekday(): 0=Mon, ..., 6=Sun)
OPEN_WEEKDAYS = {
    'wilmington': {1, 3, 5},  # Tue, Thu, Sat
    'chinatown': {0, 2, 4},   # Mon, Wed, Fri
}

# Start times patients can pick online: every 30 minutes from 9:00 to 17:30.
# (The clinic has yet to confirm whether 9:00, 9:30, the 12:00-13:00 lunch
# slots and 17:30 should stay bookable; adjust this list when it does.)
OPEN_SLOTS = [time(hour, minute) for hour in range(9, 18) for minute in (0, 30)]

# No same-day online booking; booking for the next day closes at this time
# (clinic time), so every booking is in before the clinic's evening review.
BOOKING_CUTOFF = time(18, 0)
TEXT_BOOKING_PHONE = '(978) 729-5878'
TEXT_BOOKING_PHONE_LINK = '+19787295878'

BOOKING_CUTOFF_LABEL = BOOKING_CUTOFF.strftime('%I:%M %p').lstrip('0')  # e.g. '6:00 PM'
BOOKING_NOTICE = (
    f'Please book online by {BOOKING_CUTOFF_LABEL} the day before your visit. '
    f'For same-day or last-minute appointments, please text us at {TEXT_BOOKING_PHONE}.'
)
BOOKING_CLOSED_MESSAGE = 'Online booking for this date has closed. ' + BOOKING_NOTICE
LOCATION_CLOSED_MESSAGE = 'The selected location is not open on this date. Please choose another date.'
SLOT_TAKEN_MESSAGE = 'That time was just booked by someone else. Please choose another time.'


def earliest_booking_date():
    now = timezone.localtime()
    days_ahead = 1 if now.time() < BOOKING_CUTOFF else 2
    return now.date() + timedelta(days=days_ahead)


def booking_error(selected_date, location):
    """Return why selected_date can't be booked online at location, or None."""
    if selected_date < earliest_booking_date():
        return BOOKING_CLOSED_MESSAGE
    if selected_date.weekday() not in OPEN_WEEKDAYS.get(location, ()):
        return LOCATION_CLOSED_MESSAGE
    return None


def booked_times(selected_date, location):
    """Times already taken on a day; cancelled bookings free their slot."""
    from .models import Appointment

    return set(
        Appointment.objects.filter(date=selected_date, location=location)
        .exclude(status=Appointment.STATUS_CANCELLED)
        .values_list('time', flat=True)
    )


def available_times(selected_date, location):
    if booking_error(selected_date, location):
        return []
    taken = booked_times(selected_date, location)
    return [slot for slot in OPEN_SLOTS if slot not in taken]
