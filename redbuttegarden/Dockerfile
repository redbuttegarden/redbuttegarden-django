# Use an official Python runtime as a parent image
FROM python:3.12
LABEL maintainer="avery.uslaner@redbutte.utah.edu"

# Set environment varibles
ENV PYTHONUNBUFFERED=1
ENV DJANGO_ENV=dev

RUN apt update && apt install -y libpq-dev  # Dependency for psycopg2

COPY ./requirements.txt /code/requirements.txt
RUN pip install --upgrade pip
# Install any needed packages specified in requirements.txt
RUN pip install -r /code/requirements.txt
RUN pip install django-debug-toolbar

# Copy the current directory contents into the container at /code/
COPY . /code/
# Set the working directory to /code/
WORKDIR /code/
