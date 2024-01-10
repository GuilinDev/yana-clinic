from django.db import models

class Appointment(models.Model):
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    email = models.EmailField()
    address = models.CharField(max_length=200, blank=True)
    date = models.DateField()
    time = models.TimeField()  # Assuming this represents the appointment time
    message = models.TextField(blank=True)

    def __str__(self):
        return f"Appointment for {self.name} on {self.date} at {self.time}"
