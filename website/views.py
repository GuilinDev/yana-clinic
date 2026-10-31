import ipaddress
import logging
from datetime import datetime

from django.core.cache import cache
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods, require_safe

from .booking import (
    BOOKING_CLOSED_MESSAGE,
    BOOKING_CUTOFF_LABEL,
    LOCATIONS,
    SLOT_TAKEN_MESSAGE,
    TEXT_BOOKING_PHONE,
    TEXT_BOOKING_PHONE_LINK,
    available_times,
    booked_times,
    earliest_booking_date,
)
from .forms import AppointmentForm

logger = logging.getLogger(__name__)

# Booking attempts allowed per client address per hour. A backstop behind the
# honeypot field, so generous enough never to touch real patients.
BOOKING_RATE_LIMIT = 30
RATE_LIMIT_MESSAGE = (
    f'Too many booking attempts from your connection. Please try again in an hour '
    f'or text us at {TEXT_BOOKING_PHONE}.'
)


def booking_context():
    return {
        'booking_min_date': earliest_booking_date().isoformat(),
        'booking_cutoff_label': BOOKING_CUTOFF_LABEL,
        'booking_closed_message': BOOKING_CLOSED_MESSAGE,
        'text_phone': TEXT_BOOKING_PHONE,
        'text_phone_link': TEXT_BOOKING_PHONE_LINK,
        'locations': LOCATIONS,
    }


def client_address(request):
    """The client's public IP, or None when it can't be told apart from the proxy."""
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR', '')
    # The last entry is the one appended by our own proxy; earlier ones are client-supplied
    candidate = forwarded.split(',')[-1].strip() if forwarded else request.META.get('REMOTE_ADDR', '')
    try:
        address = ipaddress.ip_address(candidate)
    except ValueError:
        return None
    if address.is_loopback or address.is_private or address.is_link_local:
        return None
    return str(address)


def rate_limited(request):
    address = client_address(request)
    if address is None:
        return False
    key = f'booking-rate:{address}'
    cache.add(key, 0, timeout=3600)
    try:
        attempts = cache.incr(key)
    except ValueError:  # key expired between add and incr
        attempts = 1
    return attempts > BOOKING_RATE_LIMIT


def appointment_payload(appointment):
    location = LOCATIONS.get(appointment.location, LOCATIONS['wilmington'])
    return {
        'date': appointment.date.isoformat(),
        'date_display': appointment.date.strftime('%A, %B %-d, %Y'),
        'time': appointment.time.strftime('%H:%M'),
        'time_display': appointment.time.strftime('%-I:%M %p'),
        'service': appointment.service,
        'location': appointment.location,
        'location_name': location['name'],
        'address': location['address'],
        'phone': location['phone'],
        'phone_link': location['phone_link'],
    }


@require_http_methods(['GET', 'HEAD', 'POST'])
def home(request):
    if request.method != 'POST':
        return render(request, 'home.html', booking_context())

    if rate_limited(request):
        return JsonResponse({'ok': False, 'error': RATE_LIMIT_MESSAGE}, status=429)

    form = AppointmentForm(request.POST, prefix='your')
    if not form.is_valid():
        errors = form.prefixed_errors()
        first_error = next(iter(errors.values()))[0]
        return JsonResponse({'ok': False, 'error': first_error, 'errors': errors}, status=400)

    if form.is_bot:
        # Answer like a success so the bot learns nothing, but save nothing
        logger.info('Ignored a booking submission that filled the honeypot field')
        return JsonResponse({'ok': True, 'appointment': appointment_payload(form.instance)})

    # SQLite transactions start in IMMEDIATE mode (see settings), so the
    # check-then-insert below is serialised and two patients can't take one slot.
    with transaction.atomic():
        if form.cleaned_data['time'] in booked_times(form.cleaned_data['date'], form.cleaned_data['location']):
            return JsonResponse(
                {'ok': False, 'error': SLOT_TAKEN_MESSAGE, 'errors': {'your-time': [SLOT_TAKEN_MESSAGE]}},
                status=409,
            )
        appointment = form.save()

    # Keep patient details out of the logs; the id is enough to find the record
    logger.info(
        'New appointment #%s on %s at %s @ %s',
        appointment.pk, appointment.date, appointment.time.strftime('%H:%M'), appointment.get_location_display(),
    )
    return JsonResponse({'ok': True, 'appointment': appointment_payload(appointment)})


@require_safe
def get_available_times(request):
    date_str = request.GET.get('date')
    location = request.GET.get('location', 'wilmington')

    if not date_str:
        return JsonResponse({'error': 'Date is required'}, status=400)
    try:
        selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return JsonResponse({'error': 'Invalid date format'}, status=400)

    return JsonResponse({
        'available_times': [slot.strftime('%H:%M') for slot in available_times(selected_date, location)],
    })
