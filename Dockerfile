# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /usr/src/app

# Install dependencies
COPY requirements.txt /usr/src/app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . /usr/src/app/

# Expose the port the app runs on
EXPOSE 8000

# Start Gunicorn with 3 workers
CMD ["gunicorn", "--workers=3", "--bind=0.0.0.0:8000", "your_project_name.wsgi:application"]
