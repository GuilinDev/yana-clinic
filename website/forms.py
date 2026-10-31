import re

from django import forms

from .booking import OPEN_SLOTS, booking_error
from .models import Appointment


class AppointmentForm(forms.ModelForm):
    """Validates the public booking form. Field names carry the 'your-' prefix
    used by the template (pass prefix='your')."""

    # Honeypot: hidden from people, filled in by bots. Never saved.
    website = forms.CharField(required=False)

    class Meta:
        model = Appointment
        fields = ['name', 'phone', 'email', 'service', 'date', 'time', 'location', 'message']
        error_messages = {
            'name': {'required': 'Please enter your name.'},
            'phone': {'required': 'Please enter your phone number.'},
            'email': {'required': 'Please enter your email address.', 'invalid': 'Please enter a valid email address.'},
            'service': {'required': 'Please select a service.'},
            'date': {'required': 'Please select a date.', 'invalid': 'Please select a valid date.'},
            'time': {'required': 'Please select a time.', 'invalid': 'Please choose a time from the list.'},
            'location': {'required': 'Please select a location.', 'invalid_choice': 'Please select a location.'},
        }

    def clean_name(self):
        name = ' '.join(self.cleaned_data['name'].split())
        if len(name) < 2:
            raise forms.ValidationError('Please enter your name.')
        return name

    def clean_phone(self):
        raw = self.cleaned_data['phone'].strip()
        digits = re.sub(r'\D', '', raw)
        if digits.startswith('1') and len(digits) == 11:
            digits = digits[1:]
        if len(digits) == 10:
            return f'({digits[:3]}) {digits[3:6]}-{digits[6:]}'
        if 10 <= len(digits) <= 15:
            return '+' + digits
        raise forms.ValidationError('Please enter a valid phone number.')

    def clean_time(self):
        value = self.cleaned_data['time']
        if value not in OPEN_SLOTS:
            raise forms.ValidationError('Please choose a time from the list.')
        return value

    def clean(self):
        cleaned = super().clean()
        date, location = cleaned.get('date'), cleaned.get('location')
        if date and location:
            error = booking_error(date, location)
            if error:
                self.add_error('date', error)
        return cleaned

    @property
    def is_bot(self):
        return bool(self.cleaned_data.get('website'))

    def prefixed_errors(self):
        """Errors keyed the way the template names its inputs (your-name, ...)."""
        return {
            ('form' if field == '__all__' else f'{self.prefix}-{field}'): list(messages)
            for field, messages in self.errors.items()
        }
