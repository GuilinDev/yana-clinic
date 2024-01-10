# Generated by Django 5.0 on 2024-01-05 02:26

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Appointment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('phone', models.CharField(max_length=15)),
                ('email', models.EmailField(max_length=254)),
                ('address', models.CharField(blank=True, max_length=200)),
                ('date', models.DateField()),
                ('time', models.TimeField()),
                ('message', models.TextField(blank=True)),
            ],
        ),
    ]
