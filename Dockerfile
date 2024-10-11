# Use Python base image
FROM mcr.microsoft.com/devcontainers/python:1-3.12-bookworm

# Prevents Python from buffering outputs (important for logging in containers)
ENV PYTHONUNBUFFERED=1

# Set the working directory inside the container
WORKDIR /app

# Copy requirements file first (leveraging Docker's cache to avoid reinstalling dependencies unnecessarily)
COPY requirements.txt /app/requirements.txt

# Install pip and project dependencies
RUN pip3 install --upgrade pip
RUN pip3 install -r /app/requirements.txt

# Copy the entire project into the container
COPY . /app

# Expose the application port
EXPOSE 8000