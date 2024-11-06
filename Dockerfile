FROM public.ecr.aws/lambda/python:3.8

LABEL maintainer="avery.uslaner@redbutte.utah.edu"

# Set environment varibles
ENV PYTHONUNBUFFERED=1
ENV DJANGO_ENV=production

RUN yum install -y gcc postgresql-devel python3.8-distutils

COPY redbuttegarden/requirements.txt ${LAMBDA_TASK_ROOT}

RUN pip install --upgrade pip setuptools
RUN pip install -r requirements.txt

COPY redbuttegarden ${LAMBDA_TASK_ROOT}