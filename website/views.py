from datetime import datetime, timedelta

from django.core.mail import send_mail
from django.http import JsonResponse
from django.shortcuts import render

from .models import Appointment


def home(request):
    if request.method == 'POST':
        # Extracting form data
        name = request.POST['your-name']
        phone = request.POST['your-phone']
        email = request.POST['your-email']
        address = request.POST.get('your-address', '')
        date = request.POST['your-date']
        time = request.POST['your-time']
        message = request.POST.get('your-message', '')

        # Creating a new appointment
        appointment = Appointment(
            name=name,
            phone=phone,
            email=email,
            address=address,
            date=datetime.strptime(date, '%Y-%m-%d').date(),
            time=datetime.strptime(time, '%H:%M').time(),
            message=message
        )
        appointment.save()

        # Send an email for the appointment
        send_mail(
            f'Appointment for {name} on {date} at {time}',  # subject
            f'You have an appointment for {name} on {date} at {time}.',  # message
            email,  # from email
            ['blessandjoywellness@gmail.com'],  # to email
            fail_silently=False,
        )

        # for contact form
        # print(request.POST)
        # message_name = request.POST['message-name']
        # message_email = request.POST['message-email']
        # message = request.POST['message']

        # Send an email
        # send_mail(
        #     message_name, # subject
        #     message, # message
        #     message_email, # from email
        #     ['guilindev@gmail.com'], # to email
        #     fail_silently=False,
        # )
        return render(request, 'home.html', {'message_name': name})
    else:
        return render(request, 'home.html', {})


from datetime import datetime, timedelta


def get_available_times(request):
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
        appointment_time = datetime.combine(selected_date, datetime.time(hour=hour, minute=minute))
        if not booked_appointments.filter(time=appointment_time.time()).exists():
            available_times.append(appointment_time.strftime('%H:%M'))

    return JsonResponse({'available_times': available_times})
