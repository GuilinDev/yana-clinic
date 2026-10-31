import logging
from datetime import datetime, time, timedelta

from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone

from .models import Appointment

logger = logging.getLogger(__name__)

LOCATIONS = {
    'wilmington': {
        'name': 'Wilmington',
        'address': '420 Main Street, Wilmington, MA 01887',
        'phone': '(978) 729-5878',
    },
    'chinatown': {
        'name': 'Chinatown (Boston)',
        'address': '65 Harrison Ave. Suite 201B, Boston, MA 02111',
        'phone': '(617) 451-7500',
    },
}

# Open days per location (Python weekday(): 0=Mon, ..., 6=Sun)
OPEN_WEEKDAYS = {
    'wilmington': {1, 3, 5},  # Tue, Thu, Sat
    'chinatown': {0, 2, 4},   # Mon, Wed, Fri
}

# No same-day online booking; booking for the next day closes at this time
# (clinic time), so every booking is in before the clinic's evening review.
BOOKING_CUTOFF = time(18, 0)
TEXT_BOOKING_PHONE = '(978) 729-5878'

_cutoff_label = BOOKING_CUTOFF.strftime('%I:%M %p').lstrip('0')  # e.g. '6:00 PM'
BOOKING_NOTICE = (
    f'Please book online by {_cutoff_label} the day before your visit. '
    f'For same-day or last-minute appointments, please text us at {TEXT_BOOKING_PHONE}.'
)
BOOKING_CLOSED_MESSAGE = 'Online booking for this date has closed. ' + BOOKING_NOTICE


def earliest_booking_date():
    now = timezone.localtime()
    days_ahead = 1 if now.time() < BOOKING_CUTOFF else 2
    return now.date() + timedelta(days=days_ahead)


def booking_error(selected_date, location):
    """Return why selected_date can't be booked online at location, or None."""
    if selected_date < earliest_booking_date():
        return BOOKING_CLOSED_MESSAGE
    if selected_date.weekday() not in OPEN_WEEKDAYS.get(location, ()):
        return 'The selected location is not open on this date. Please choose another date.'
    return None


def booking_context():
    return {
        'booking_min_date': earliest_booking_date().isoformat(),
        'booking_notice': BOOKING_NOTICE,
        'booking_closed_message': BOOKING_CLOSED_MESSAGE,
    }


def home(request):
    if request.method == 'POST':
        name = request.POST['your-name']
        phone = request.POST['your-phone']
        email = request.POST['your-email']
        service = request.POST['your-service']
        date = request.POST['your-date']
        time_str = request.POST['your-time']
        location = request.POST.get('your-location', 'wilmington')
        message = request.POST.get('your-message', '')

        try:
            appointment_date = datetime.strptime(date, '%Y-%m-%d').date()
        except ValueError:
            return JsonResponse({'error': 'Invalid date.'}, status=400)
        error = booking_error(appointment_date, location)
        if error:
            return JsonResponse({'error': error}, status=400)

        appointment = Appointment(
            name=name,
            phone=phone,
            email=email,
            service=service,
            date=appointment_date,
            time=datetime.strptime(time_str, '%H:%M').time(),
            location=location,
            message=message,
        )
        appointment.save()

        loc_info = LOCATIONS.get(location, LOCATIONS['wilmington'])
        # Keep patient details out of the logs; the id is enough to find the record
        logger.info('New appointment #%s on %s at %s @ %s', appointment.pk, date, time_str, loc_info['name'])

        return render(request, 'home.html', {
            **booking_context(),
            'message_name': name,
            'message_location': loc_info['name'],
            'message_address': loc_info['address'],
        })
    else:
        return render(request, 'home.html', booking_context())


def get_available_times(request):
    date_str = request.GET.get('date')
    location = request.GET.get('location', 'wilmington')

    if not date_str:
        return JsonResponse({'error': 'Date is required'}, status=400)

    try:
        selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return JsonResponse({'error': 'Invalid date format'}, status=400)

    if booking_error(selected_date, location):
        return JsonResponse({'available_times': []})

    # Working hours: 9:00 - 17:30, every 30 min
    working_hours = [(hour, minute) for hour in range(9, 18) for minute in [0, 30]]

    # Filter by date AND location
    booked_appointments = Appointment.objects.filter(date=selected_date, location=location)

    available_times = []
    for hour, minute in working_hours:
        t = time(hour=hour, minute=minute)
        if not booked_appointments.filter(time=t).exists():
            available_times.append(f'{hour:02d}:{minute:02d}')

    return JsonResponse({'available_times': available_times})
