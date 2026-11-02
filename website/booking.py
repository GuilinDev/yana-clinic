"""Booking rules shared by the views, the form, the emails and the templates.

Everything about when the clinic can be booked online lives here, in one place.
"""
from collections import Counter
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

# Start times patients can pick online: on the hour from 9:00, last start 16:00,
# no lunch break (confirmed by the clinic, Nov 2026).
OPEN_SLOTS = [time(hour, 0) for hour in range(9, 17)]

# How many patients each start time can take. Wilmington treats two at a time.
SLOT_CAPACITY = {
    'wilmington': 2,
    'chinatown': 1,
}

# No same-day online booking; booking for the next day closes at this time
# (clinic time), so every booking is in before the clinic's evening review.
BOOKING_CUTOFF = time(18, 0)
TEXT_BOOKING_PHONE = '(978) 729-5878'
TEXT_BOOKING_PHONE_LINK = '+19787295878'
# The clinic confirms every online booking by text message from this number
CONFIRM_PHONE = TEXT_BOOKING_PHONE
CONFIRM_PHONE_LINK = TEXT_BOOKING_PHONE_LINK

BOOKING_CUTOFF_LABEL = BOOKING_CUTOFF.strftime('%I:%M %p').lstrip('0')  # e.g. '6:00 PM'
BOOKING_NOTICE = (
    f'Please book online by {BOOKING_CUTOFF_LABEL} the day before your visit. '
    f'For same-day or last-minute appointments, please text us at {TEXT_BOOKING_PHONE}.'
)
BOOKING_CLOSED_MESSAGE = 'Online booking for this date has closed. ' + BOOKING_NOTICE
LOCATION_CLOSED_MESSAGE = 'The selected location is not open on this date. Please choose another date.'
SLOT_TAKEN_MESSAGE = 'That time was just filled by another booking. Please choose another time.'


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


def slot_capacity(location):
    return SLOT_CAPACITY.get(location, 1)


def booked_counts(selected_date, location):
    """Active bookings per start time on a day; cancelled bookings free their place."""
    from .models import Appointment

    times = (
        Appointment.objects.filter(date=selected_date, location=location)
        .exclude(status=Appointment.STATUS_CANCELLED)
        .values_list('time', flat=True)
    )
    return Counter(times)


def slot_is_full(selected_date, slot, location):
    return booked_counts(selected_date, location)[slot] >= slot_capacity(location)


def available_times(selected_date, location):
    if booking_error(selected_date, location):
        return []
    counts = booked_counts(selected_date, location)
    capacity = slot_capacity(location)
    return [slot for slot in OPEN_SLOTS if counts[slot] < capacity]
