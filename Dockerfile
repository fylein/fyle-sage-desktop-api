# Pull python base image
FROM python:3.11-slim

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get update && apt-get -y install libpq-dev gcc && apt-get install git -y --no-install-recommends

# Installing requirements
COPY requirements.txt /tmp/requirements.txt
RUN pip install --upgrade pip && pip install -r /tmp/requirements.txt && pip install flake8

# Copy Project to the container
RUN mkdir -p /fyle-sage-desktop-api
COPY . /fyle-sage-desktop-api/
WORKDIR /fyle-sage-desktop-api

# Do linting checks
RUN flake8 .

# Expose development port
EXPOSE 8000

# Run development server
CMD /bin/bash run.sh
