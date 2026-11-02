import os
from email.utils import formataddr
from pathlib import Path
from decouple import Csv, config
from django.core.exceptions import ImproperlyConfigured

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Defaults are the production-safe ones; local development sets DEBUG=True in .env
# (see .env.example). The deploy script generates SECRET_KEY once on the server.
DEBUG = config('DEBUG', default=False, cast=bool)

SECRET_KEY = config('SECRET_KEY', default='')
if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = 'django-insecure-local-development-only'
    else:
        raise ImproperlyConfigured('SECRET_KEY must be set when DEBUG is False')

ALLOWED_HOSTS = config(
    'ALLOWED_HOSTS',
    default='blessandjoywellness.com,www.blessandjoywellness.com,64.176.216.79,localhost,127.0.0.1',
    cast=Csv(),
)

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'website',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'clinic.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'clinic.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
        'OPTIONS': {
            # Take the write lock when a transaction starts, so check-then-insert
            # inside transaction.atomic() can't double-book a slot
            'transaction_mode': 'IMMEDIATE',
            'timeout': 20,
        },
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'America/New_York'
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = 'static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage'},
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        '': {
            'handlers': ['console'],
            'level': config('LOG_LEVEL', default='INFO'),
            'propagate': True,
        },
    },
}

CSRF_TRUSTED_ORIGINS = ['https://blessandjoywellness.com', 'https://www.blessandjoywellness.com']
SESSION_COOKIE_DOMAIN = config('SESSION_COOKIE_DOMAIN', default=None)

# Email: booking notifications to the clinic and confirmations to patients.
# Nothing is sent until EMAIL_HOST_PASSWORD is set (the deploy script copies the
# EMAIL_* GitHub secrets into the server's clinic.env). Works with Gmail SMTP
# (an app password) or any SMTP relay such as Resend.
EMAIL_BACKEND = config(
    'EMAIL_BACKEND',
    default='django.core.mail.backends.console.EmailBackend' if DEBUG else 'django.core.mail.backends.smtp.EmailBackend',
)
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
EMAIL_TIMEOUT = 15
# The sender address; a bare address gets the clinic's name as display name.
# (With an SMTP relay such as Resend, EMAIL_HOST_USER is not an address.)
_from_email = config(
    'DEFAULT_FROM_EMAIL',
    default=EMAIL_HOST_USER if '@' in EMAIL_HOST_USER else 'blessandjoywellness@gmail.com',
)
DEFAULT_FROM_EMAIL = _from_email if '<' in _from_email else formataddr(('Bless and Joy Wellness', _from_email))
SERVER_EMAIL = DEFAULT_FROM_EMAIL
SITE_URL = config('SITE_URL', default='https://blessandjoywellness.com')
BOOKING_NOTIFY_EMAIL = config('BOOKING_NOTIFY_EMAIL', default='blessandjoywellness@gmail.com')
BOOKING_EMAILS_ENABLED = config('BOOKING_EMAILS_ENABLED', default=bool(EMAIL_HOST_PASSWORD) or DEBUG, cast=bool)
BOOKING_EMAILS_IN_BACKGROUND = config('BOOKING_EMAILS_IN_BACKGROUND', default=True, cast=bool)

# TLS is terminated by the reverse proxy in front of the container. Only send
# cookies over HTTPS outside local development. (HSTS and the HTTPS redirect are
# left to the proxy until its configuration has been confirmed.)
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
