# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Yana Clinic (Bless and Joy Wellness) is a Django 5.0 web application for a wellness clinic with two locations (Wilmington and Chinatown Boston). It handles appointment booking and serves a public-facing website at blessandjoywellness.com.

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Local settings (DEBUG=True etc.). Defaults are production-safe: without a .env,
# DEBUG is False and SECRET_KEY is required.
cp .env.example .env

# Run development server
python manage.py runserver

# Database migrations
python manage.py makemigrations
python manage.py migrate

# Collect static files (for deployment)
python manage.py collectstatic

# Production server (used in Procfile)
gunicorn clinic.wsgi

# Run tests (website/tests.py)
python manage.py test

# Back up the SQLite database (used by the nightly cron on the server)
python manage.py backup_db --dest /path/to/backups --keep 14
```

There is no linter configured in this project.

## Architecture

- **Django project**: `clinic/` — settings, root URL config, WSGI/ASGI entry points
- **Single app**: `website/` — all business logic lives here
- **Database**: SQLite (`db.sqlite3`, not committed), single model `Appointment` (name, phone, email, service, date, time, location, message, status, notes, created_at). SQLite transactions start in `IMMEDIATE` mode so booking inserts are serialised
- **Static files**: served via WhiteNoise from `static/website/`
- **Templates**: `website/templates/` (home.html, login.html). The booking form's script is inline at the bottom of home.html; it shows errors next to fields, fills the success modal from the JSON response and offers an `.ics` calendar link. Phone numbers and the email address are `tel:` / `sms:` / `mailto:` links
- **Config**: `python-decouple` reads `.env` / environment variables: `DEBUG` (default False), `SECRET_KEY` (required unless DEBUG), `ALLOWED_HOSTS` (comma-separated, defaults to the production hosts + localhost), `SESSION_COOKIE_DOMAIN`, `LOG_LEVEL`. Cookies are Secure whenever DEBUG is False; TLS is terminated by the reverse proxy on the server.

### Key Files

- `website/booking.py` — Every booking rule in one place: `LOCATIONS`, `OPEN_WEEKDAYS`, `OPEN_SLOTS` (9:00–17:30 every 30 min, pending the clinic's confirmation of 9:00/9:30, lunch and 17:30), `BOOKING_CUTOFF`, `booking_error`, `available_times`
- `website/forms.py` — `AppointmentForm` (ModelForm, used with `prefix='your'` so field names match the template: `your-name`, …). Validates phone/time/date rules and carries the `website` honeypot field
- `website/views.py` — `home`: GET renders the page; POST is a JSON API used by the page's script: `{ok: true, appointment: {...}}` on success, `{ok: false, error, errors: {'your-field': [...]}}` with 400 (validation), 409 (slot just taken) or 429 (rate limit: `BOOKING_RATE_LIMIT` attempts per public IP per hour, skipped when the client IP can't be told apart from the proxy). Honeypot submissions get a fake success and are not saved. `get_available_times` returns the free slots for a date and location (cancelled bookings free their slot)
- `website/admin.py` — appointment list with status (editable inline), date hierarchy, filters, CSV export and mark-confirmed/cancelled actions
- `website/management/commands/backup_db.py` — SQLite online backup with pruning, run nightly on the server
- `website/utils.py` — Placeholder for future email service integration
- `clinic/urls.py` — Admin at `/yana/`, auth views at `/accounts/login/` and `/logout/`

### Two Clinic Locations

- **Wilmington**: 420 Main St, Wilmington, MA 01887 — Open Tue/Thu/Sat
- **Chinatown**: 65 Harrison Ave. Suite 201B, Boston, MA 02111 — Open Mon/Wed/Fri
- Both closed on Sunday and holidays
- Appointment booking includes location selector; date validation enforces correct days per location
- No same-day online booking; booking for the next day closes at 6:00 PM (America/New_York) the day before, so the clinic sees every booking in its evening review. Patients are told to text (978) 729-5878 instead

### Deployment

- GitHub Actions (`.github/workflows/build.yaml`) on push to `main`: `test` job (checks + tests on Python 3.13) → `docker` job builds the image and pushes `guilindev/clinic:latest` and `guilindev/clinic:<commit sha>` → `deploy` job SSHes into Vultr
- Runs on Vultr at 64.176.216.79 (Ubuntu 22.04), container `clinic` on port 8000 behind a reverse proxy
- Files on the server: `/root/clinic-data/db.sqlite3` (bind-mounted into the container), `/root/clinic-data/clinic.env` (holds `SECRET_KEY`, generated once by the deploy script, passed with `--env-file`), `/root/clinic-backups/` (`pre-deploy-*.sqlite3` snapshots taken by every deploy, 10 kept; nightly `db-*.sqlite3` from `/etc/cron.d/clinic-backup` via `manage.py backup_db`, 14 kept)
- The deploy script pulls the image first, snapshots the database, starts the new container, then health-checks `http://127.0.0.1:8000/` for up to 60 s. On failure it restarts the previous image (`guilindev/clinic:previous`) and fails the run.
- **Rollback**: Actions → build-and-deploy → "Run workflow" → `image_tag` = the commit SHA of a known-good run (no rebuild, same health check). On the server: `docker stop clinic && docker rm clinic`, then start `guilindev/clinic:previous` or any `guilindev/clinic:<sha>` with the `docker run` command from the workflow. To restore data, copy a snapshot from `/root/clinic-backups/` over `/root/clinic-data/db.sqlite3` while the container is stopped.
- Dependabot (`.github/dependabot.yml`) opens weekly PRs for pip, GitHub Actions and the Docker base image.
