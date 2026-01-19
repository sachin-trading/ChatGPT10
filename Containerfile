# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Set the working directory in the container
WORKDIR /app

# Install dependencies first (for better caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Define environment variables (should be overridden during deployment)
ENV FYERS_CLIENT_ID=""
ENV FYERS_SECRET_KEY=""
ENV ACCESS_TOKEN=""

# Run main.py when the container launches
CMD ["python", "main.py"]
