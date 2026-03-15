# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Yana Clinic (Bless and Joy Wellness) is a Django 5.0 web application for a wellness clinic with two locations (Wilmington and Chinatown Boston). It handles appointment booking and serves a public-facing website at blessandjoywellness.com.

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run development server
python manage.py runserver

# Database migrations
python manage.py makemigrations
python manage.py migrate

# Collect static files (for deployment)
python manage.py collectstatic

# Production server (used in Procfile)
gunicorn clinic.wsgi
```

There is no test suite or linter configured in this project.

## Architecture

- **Django project**: `clinic/` — settings, root URL config, WSGI/ASGI entry points
- **Single app**: `website/` — all business logic lives here
- **Database**: SQLite (`db.sqlite3`), single model `Appointment` (name, phone, email, service, date, time, location, message)
- **Static files**: served via WhiteNoise from `static/website/`
- **Templates**: `website/templates/` (home.html, login.html)
- **Config**: Uses `python-decouple` for SECRET_KEY, DEBUG, SESSION_COOKIE_DOMAIN via environment variables

### Key Files

- `website/views.py` — Two views: `home` (renders page + handles POST appointment form with location), `get_available_times` (AJAX endpoint returning available 30-min slots from 9:00–17:30, filtered by location)
- `website/utils.py` — Placeholder for future email service integration
- `clinic/urls.py` — Admin at `/yana/`, auth views at `/accounts/login/` and `/logout/`

### Two Clinic Locations

- **Wilmington**: 420 Main St, Wilmington, MA 01887 — Open Tue/Thu/Sat
- **Chinatown**: 65 Harrison Ave. Suite 201B, Boston, MA 02111 — Open Mon/Wed/Fri
- Both closed on Sunday and holidays
- Appointment booking includes location selector; date validation enforces correct days per location

### Deployment

- GitHub Actions (`.github/workflows/build.yaml`) on push to `main`: builds Docker image → pushes to DockerHub (`guilindev/clinic:latest`) → SSHes into Vultr to deploy
- Runs on Vultr at 64.176.216.79 (Ubuntu 22.04)
- SQLite database persisted via Docker volume mount at `/root/clinic-data/db.sqlite3`
- Environment variables configured on server: SECRET_KEY, DEBUG=False, SESSION_COOKIE_DOMAIN
