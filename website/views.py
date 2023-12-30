from django.shortcuts import render
from django.core.mail import send_mail


def home(request):
    if request.method == 'POST':
        print(request.POST)
        message_name = request.POST['message-name']
        message_email = request.POST['message-email']
        message = request.POST['message']

        # Send an email
        send_mail(
            message_name, # subject
            message, # message
            message_email, # from email
            ['guilindev@gmail.com'], # to email
            fail_silently=False,
        )
        return render(request, 'home.html', {'message_name': message_name})
    else:
        return render(request, 'home.html', {})
