import logging
from datetime import datetime, time

from django.http import JsonResponse
from django.shortcuts import render

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

        appointment = Appointment(
            name=name,
            phone=phone,
            email=email,
            service=service,
            date=datetime.strptime(date, '%Y-%m-%d').date(),
            time=datetime.strptime(time_str, '%H:%M').time(),
            location=location,
            message=message,
        )
        appointment.save()

        loc_info = LOCATIONS.get(location, LOCATIONS['wilmington'])
        logger.info(f'New appointment: {name} on {date} at {time_str} @ {loc_info["name"]}')

        return render(request, 'home.html', {
            'message_name': name,
            'message_location': loc_info['name'],
            'message_address': loc_info['address'],
        })
    else:
        return render(request, 'home.html', {})


def get_available_times(request):
    date_str = request.GET.get('date')
    location = request.GET.get('location', 'wilmington')

    if not date_str:
        return JsonResponse({'error': 'Date is required'}, status=400)

    try:
        selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return JsonResponse({'error': 'Invalid date format'}, status=400)

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
