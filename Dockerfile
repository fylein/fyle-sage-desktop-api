# Pull python base image
FROM python:3.11-slim

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get update && apt-get -y install libpq-dev gcc && apt-get install git postgresql-client curl -y --no-install-recommends

# Installing requirements
COPY requirements.txt /tmp/requirements.txt
RUN pip install --upgrade pip && pip install -r /tmp/requirements.txt && pip install flake8

# Copy Project to the container
RUN mkdir -p /fyle-sage-desktop-api
COPY . /fyle-sage-desktop-api/
WORKDIR /fyle-sage-desktop-api

# Do linting checks
RUN flake8 .

#================================================================
# Set default GID if not provided during build
#================================================================
ARG SERVICE_GID=1001

#================================================================
# Setup non-root user and permissions
#================================================================
RUN groupadd -r -g ${SERVICE_GID} sage_desktop_service && \
    useradd -r -g sage_desktop_service sage_desktop_user && \
    chown -R sage_desktop_user:sage_desktop_service /fyle-sage-desktop-api

# Switch to non-root user
USER sage_desktop_user

# Expose development port
EXPOSE 8000

# Run development server
CMD /bin/bash run.sh
