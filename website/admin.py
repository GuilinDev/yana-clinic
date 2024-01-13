from django.contrib import admin
from .models import Appointment


# Register your models here.
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'email', 'date', 'time', 'service', 'message')
    list_filter = ('date', 'service')  # Add filters if needed
    search_fields = ('name', 'email')  # Add search functionality


admin.site.register(Appointment, AppointmentAdmin)
