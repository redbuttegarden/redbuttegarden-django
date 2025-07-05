FROM public.ecr.aws/lambda/python:3.12

LABEL maintainer="avery.uslaner@redbutte.utah.edu"

# Set environment varibles
ENV PYTHONUNBUFFERED=1
ENV DJANGO_ENV=production

RUN dnf install -y gcc postgresql-devel

# Setup Python environment
ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

COPY redbuttegarden/requirements.txt .
# Activate the virtual environment and install dependencies
RUN . $VIRTUAL_ENV/bin/activate && \
    pip install --upgrade pip && \
    pip install --no-cache-dir wheel && \
    pip install --no-cache-dir --upgrade setuptools
RUN pip install --no-cache-dir -r requirements.txt

COPY ./redbuttegarden /var/task
