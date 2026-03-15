from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('website', '0002_remove_appointment_address_appointment_service'),
    ]

    operations = [
        migrations.AddField(
            model_name='appointment',
            name='location',
            field=models.CharField(
                choices=[('wilmington', 'Wilmington'), ('chinatown', 'Chinatown (Boston)')],
                default='wilmington',
                max_length=20,
            ),
        ),
    ]
