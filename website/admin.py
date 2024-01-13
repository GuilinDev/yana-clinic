from django.contrib import admin
from .models import Appointment


# Register your models here.
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'date', 'time', 'service')  # Adjust the fields as per your model
    list_filter = ('date', 'service')  # Add filters if needed
    search_fields = ('name', 'email')  # Add search functionality


admin.site.register(Appointment, AppointmentAdmin)
