# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Django 5.0 wellness clinic appointment booking system for Bless and Joy Wellness. The application handles appointment scheduling with time slot management, email notifications, and admin interface.

## Essential Commands

### Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Create superuser for admin access
python manage.py createsuperuser

# Run development server
python manage.py runserver

# Collect static files for production
python manage.py collectstatic --noinput
```

### Testing
```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test website
```

### Database
```bash
# Make migrations after model changes
python manage.py makemigrations

# Show migration SQL
python manage.py sqlmigrate website <migration_number>

# Access Django shell
python manage.py shell
```

## Architecture

### Core Components

1. **`clinic/`** - Django project configuration
   - `settings.py` - Contains all configuration including AWS services, email settings, and security settings
   - `urls.py` - Root URL routing, admin at `/yana/`

2. **`website/`** - Main appointment booking application
   - `models.py` - `Appointment` model with fields: name, phone, email, service, date, time, message
   - `views.py` - `home` view handles appointment form submission and time slot availability
   - `utils.py` - AWS integration utilities for SES email and SNS SMS (requires configuration)
   - `templates/website/` - HTML templates with Bootstrap-based responsive design

### Key Patterns

- **Time Slot Management**: The system checks existing appointments to prevent double-booking. Available slots are filtered in `views.py` based on existing appointments for the selected date.

- **Email Notifications**: Currently using console backend. Production uses AWS SES or Gmail SMTP (configuration required in settings).

- **Static Files**: Served via WhiteNoise in production. SCSS files in `static/website/scss/` compile to CSS.

- **Admin Customization**: Django admin is customized for clinic management at `/yana/` with branding for "Bless and Joy Wellness".

### Environment Configuration

Production deployment requires setting these environment variables:
- `SECRET_KEY` - Django secret key (currently hardcoded, needs change)
- `DEBUG` - Set to False for production
- `ALLOWED_HOSTS` - Restrict to actual domain
- AWS credentials for SES/SNS if using AWS services

### Database Schema

Current `Appointment` model:
- `name` (max 100 chars)
- `phone` (max 15 chars)  
- `email` (EmailField)
- `service` (max 100 chars, default: 'Not specified')
- `date` (DateField)
- `time` (TimeField)
- `message` (TextField, optional)

### Deployment

- **Docker**: Dockerfile configured with Python 3.10-slim
- **Heroku**: Procfile ready with Gunicorn
- **Static Files**: WhiteNoise configured for production static file serving

## Important Notes

- Admin interface is at `/yana/` (not the default `/admin/`)
- Time slots are hardcoded in `views.py` - modify the `available_slots` list to change available appointment times
- AWS services (SES, SNS, S3) are integrated but require credential configuration
- The system filters out past dates and fully booked time slots automatically