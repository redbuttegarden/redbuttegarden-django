FROM public.ecr.aws/lambda/python:3.12

LABEL maintainer="avery.uslaner@redbutte.utah.edu"

# Set environment varibles
ENV PYTHONUNBUFFERED=1
ENV DJANGO_ENV=production

COPY . /var/task

RUN dnf install -y gcc postgresql-devel
