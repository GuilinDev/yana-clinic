import csv

from django.contrib import admin
from django.http import HttpResponse
from django.utils import timezone

from .models import Appointment


@admin.action(description='Mark selected appointments as confirmed')
def mark_confirmed(modeladmin, request, queryset):
    queryset.update(status=Appointment.STATUS_CONFIRMED)


@admin.action(description='Mark selected appointments as cancelled')
def mark_cancelled(modeladmin, request, queryset):
    queryset.update(status=Appointment.STATUS_CANCELLED)


@admin.action(description='Download selected appointments as CSV')
def export_csv(modeladmin, request, queryset):
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="appointments-{timezone.localdate():%Y-%m-%d}.csv"'
    writer = csv.writer(response)
    writer.writerow(['Date', 'Time', 'Location', 'Status', 'Name', 'Phone', 'Email', 'Service', 'Message', 'Notes', 'Booked at'])
    for a in queryset.order_by('date', 'time'):
        writer.writerow([
            a.date, a.time.strftime('%H:%M'), a.get_location_display(), a.get_status_display(),
            a.name, a.phone, a.email, a.service, a.message, a.notes,
            timezone.localtime(a.created_at).strftime('%Y-%m-%d %H:%M'),
        ])
    return response


class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('date', 'time', 'location', 'name', 'phone', 'service', 'status', 'short_message', 'created_at')
    list_display_links = ('date', 'time', 'name')
    list_editable = ('status',)
    list_filter = ('status', 'location', 'service', 'date')
    search_fields = ('name', 'email', 'phone')
    date_hierarchy = 'date'
    ordering = ('-date', '-time')
    readonly_fields = ('created_at',)
    actions = [mark_confirmed, mark_cancelled, export_csv]
    list_per_page = 50
    fieldsets = (
        ('Appointment', {'fields': ('date', 'time', 'location', 'service', 'status')}),
        ('Patient', {'fields': ('name', 'phone', 'email', 'message')}),
        ('Clinic', {'fields': ('notes', 'created_at')}),
    )

    @admin.display(description='Message')
    def short_message(self, obj):
        text = obj.message.strip()
        return text if len(text) <= 60 else text[:57] + '...'


admin.site.register(Appointment, AppointmentAdmin)
