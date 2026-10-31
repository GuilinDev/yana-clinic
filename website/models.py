from django.db import models


class Appointment(models.Model):
    LOCATION_CHOICES = [
        ('wilmington', 'Wilmington'),
        ('chinatown', 'Chinatown (Boston)'),
    ]
    STATUS_PENDING = 'pending'
    STATUS_CONFIRMED = 'confirmed'
    STATUS_CANCELLED = 'cancelled'
    STATUS_NO_SHOW = 'no_show'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_CONFIRMED, 'Confirmed'),
        (STATUS_CANCELLED, 'Cancelled'),
        (STATUS_NO_SHOW, 'No-show'),
    ]

    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    email = models.EmailField()
    service = models.CharField(max_length=100, default='Not specified')
    date = models.DateField()
    time = models.TimeField()
    location = models.CharField(max_length=20, choices=LOCATION_CHOICES, default='wilmington')
    message = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_PENDING)
    notes = models.TextField(blank=True, help_text='Internal notes, never shown to the patient')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Appointment for {self.name} on {self.date} at {self.time} @ {self.get_location_display()}"
