"""Emails sent when a patient books online: one to the clinic, one to the patient.

Nothing here can break a booking: sending is skipped until email is configured
(settings.BOOKING_EMAILS_ENABLED) and every failure is logged, never raised.
"""
import logging
import threading
from datetime import datetime, timedelta

from django.conf import settings
from django.core.mail import EmailMessage
from django.utils import timezone

from .booking import CONFIRM_PHONE, LOCATIONS, TEXT_BOOKING_PHONE

logger = logging.getLogger(__name__)

CLINIC_NAME = 'Bless and Joy Wellness'


def notify_new_booking(appointment):
    if not settings.BOOKING_EMAILS_ENABLED:
        logger.info('Email is not configured; no notifications sent for appointment #%s', appointment.pk)
        return
    if settings.BOOKING_EMAILS_IN_BACKGROUND:
        # Don't make the patient wait for two SMTP conversations
        threading.Thread(target=send_all, args=(appointment,), name=f'booking-email-{appointment.pk}').start()
    else:
        send_all(appointment)


def send_all(appointment):
    for build in (clinic_email, patient_email):
        try:
            build(appointment).send()
        except Exception:
            logger.exception('Could not send %s for appointment #%s', build.__name__, appointment.pk)


def _details(appointment):
    location = LOCATIONS.get(appointment.location, LOCATIONS['wilmington'])
    return {
        'date': appointment.date.strftime('%A, %B %-d, %Y'),
        'time': appointment.time.strftime('%-I:%M %p'),
        'short': f'{appointment.date:%a %b %-d}, {appointment.time:%-I:%M %p}',
        'location': location,
    }


def clinic_email(appointment):
    d = _details(appointment)
    # The patient's message can contain health details, so it stays in the admin
    message_note = 'yes, see the admin' if appointment.message.strip() else 'none'
    body = (
        f'A patient booked online.\n\n'
        f'  Name:       {appointment.name}\n'
        f'  Phone:      {appointment.phone}\n'
        f'  Email:      {appointment.email}\n'
        f'  Service:    {appointment.service}\n'
        f'  Date/time:  {d["date"]} at {d["time"]}\n'
        f'  Location:   {d["location"]["name"]}\n'
        f'  Message:    {message_note}\n'
        f'  Booked at:  {timezone.localtime(appointment.created_at):%Y-%m-%d %H:%M}\n\n'
        f'Review and confirm:\n'
        f'{settings.SITE_URL}/yana/website/appointment/{appointment.pk}/change/\n'
    )
    return EmailMessage(
        subject=f'New appointment request: {d["short"]}, {d["location"]["name"]}, {appointment.name}',
        body=body,
        to=[settings.BOOKING_NOTIFY_EMAIL],
        reply_to=[appointment.email],
    )


def patient_email(appointment):
    d = _details(appointment)
    body = (
        f'Hello {appointment.name},\n\n'
        f'Thank you for your appointment request. Here are the details:\n\n'
        f'  Date:      {d["date"]}\n'
        f'  Time:      {d["time"]}\n'
        f'  Service:   {appointment.service}\n'
        f'  Location:  {d["location"]["name"]}\n'
        f'             {d["location"]["address"]}\n'
        f'  Phone:     {d["location"]["phone"]}\n\n'
        f'The clinic will confirm your appointment by text message from {CONFIRM_PHONE}.\n'
        f'To change or cancel, please text us at {TEXT_BOOKING_PHONE}.\n\n'
        f'A calendar file is attached so you can add the appointment to your calendar.\n\n'
        f'{CLINIC_NAME}\n'
        f'{settings.SITE_URL}\n'
    )
    email = EmailMessage(
        subject=f'Your appointment request at {CLINIC_NAME}: {d["short"]}',
        body=body,
        to=[appointment.email],
        reply_to=[settings.BOOKING_NOTIFY_EMAIL],
    )
    email.attach('appointment.ics', calendar_invite(appointment), 'text/calendar')
    return email


def _ics_escape(text):
    return str(text).replace('\\', '\\\\').replace(';', '\\;').replace(',', '\\,').replace('\n', '\\n')


def calendar_invite(appointment):
    """A one-hour event in clinic time, as an iCalendar file."""
    location = LOCATIONS.get(appointment.location, LOCATIONS['wilmington'])
    start = datetime.combine(appointment.date, appointment.time)
    end = start + timedelta(hours=1)
    lines = [
        'BEGIN:VCALENDAR',
        'VERSION:2.0',
        f'PRODID:-//{CLINIC_NAME}//Booking//EN',
        'BEGIN:VEVENT',
        f'UID:appointment-{appointment.pk}@blessandjoywellness.com',
        f'DTSTAMP:{timezone.now():%Y%m%dT%H%M%SZ}',
        f'DTSTART;TZID={settings.TIME_ZONE}:{start:%Y%m%dT%H%M%S}',
        f'DTEND;TZID={settings.TIME_ZONE}:{end:%Y%m%dT%H%M%S}',
        f'SUMMARY:{_ics_escape(CLINIC_NAME + " - " + appointment.service)}',
        f'LOCATION:{_ics_escape(location["address"])}',
        f'DESCRIPTION:{_ics_escape(f"Phone {location['phone']}. The clinic will confirm by text message from {CONFIRM_PHONE}.")}',
        'END:VEVENT',
        'END:VCALENDAR',
    ]
    return '\r\n'.join(lines) + '\r\n'
