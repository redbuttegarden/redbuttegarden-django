# Use an official Python runtime as a parent image
FROM python:3.8
LABEL maintainer="avery.uslaner@redbutte.utah.edu"

# Set environment varibles
ENV PYTHONUNBUFFERED=1
ENV DJANGO_ENV=dev

COPY ./requirements.txt /code/requirements.txt
RUN pip install --upgrade pip
# Install any needed packages specified in requirements.txt
RUN pip install -r /code/requirements.txt
RUN pip install gunicorn
RUN pip install django-debug-toolbar

# Copy the current directory contents into the container at /code/
COPY . /code/
# Set the working directory to /code/
WORKDIR /code/

RUN useradd wagtail
RUN chown -R wagtail /code
USER wagtail

EXPOSE 8000

