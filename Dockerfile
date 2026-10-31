# Use an official Python runtime as a parent image
FROM python:3.15-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /usr/src/app

# Install dependencies
COPY requirements.txt /usr/src/app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . /usr/src/app/

# Collect static files. The key is only needed to load settings during the
# build; the real SECRET_KEY is injected at run time.
RUN SECRET_KEY=build-only DEBUG=False python manage.py collectstatic --noinput

# Expose the port the app runs on
EXPOSE 8000

# Report container health to Docker (visible in `docker ps`)
HEALTHCHECK --interval=60s --timeout=5s --start-period=40s --retries=3 \
    CMD python -c "import sys, urllib.request; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/', timeout=4).status == 200 else 1)"

# Start Gunicorn with 3 workers
CMD ["gunicorn", "--workers=3", "--bind=0.0.0.0:8000", "clinic.wsgi:application"]
