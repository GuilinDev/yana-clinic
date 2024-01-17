from datetime import datetime, time

from django.http import JsonResponse
from django.shortcuts import render

from .models import Appointment
from .utils import send_email, send_sms, backup_to_s3


def home(request):
    if request.method == 'POST':
        # Extracting form data
        name = request.POST['your-name']
        phone = request.POST['your-phone']
        email = request.POST['your-email']
        service = request.POST['your-service']
        date = request.POST['your-date']
        time = request.POST['your-time']
        message = request.POST.get('your-message', '')

        # Creating a new appointment
        appointment = Appointment(
            name=name,
            phone=phone,
            email=email,
            service=service,
            date=datetime.strptime(date, '%Y-%m-%d').date(),
            time=datetime.strptime(time, '%H:%M').time(),
            message=message
        )
        appointment.save()

        print("Preparing to send email")
        send_email(
            'blessandjoywellness@gmail.com',  # from email
            email,  # to email
            'Appointment Confirmation',  # subject
            f'You have an appointment for {name} on {date} at {time}.'
        )

        # send_sms(
        #     phone,
        #     f'{name}, You have an appointment at Bless and Joy Wellness on {date} at {time}. '
        #     f'If you are new patient, please arrive 30 minutes early.'
        # )
        #
        # backup_to_s3(
        #     f'{name}_{date}_{time}.txt',
        #     'blessandjoywellness',
        #     f'{name}_{date}_{time}.txt'
        # )

        return render(request, 'home.html', {'message_name': name})
    else:
        return render(request, 'home.html', {})


def get_available_times(request):
    print("Inside get_available_times")
    date_str = request.GET.get('date')
    if not date_str:
        return JsonResponse({'error': 'Date is required'}, status=400)

    try:
        selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return JsonResponse({'error': 'Invalid date format'}, status=400)

    # Define working hours
    working_hours = [(hour, minute) for hour in range(9, 18) for minute in [0, 30]]

    # Get booked appointments for the selected date
    booked_appointments = Appointment.objects.filter(date=selected_date)

    # Determine available times
    available_times = []
    for hour, minute in working_hours:
        appointment_time = datetime.combine(selected_date, time(hour=hour, minute=minute))
        if not booked_appointments.filter(time=appointment_time.time()).exists():
            available_times.append(appointment_time.strftime('%H:%M'))

    return JsonResponse({'available_times': available_times})
