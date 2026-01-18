# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
# Since there isn't a requirements.txt, we will install them directly
RUN pip install --no-cache-dir fyers-apiv3 pandas numpy

# Copy the current directory contents into the container at /app
COPY . .

# Create an empty bot.log file
RUN touch bot.log

# Define environment variables (these should be overridden at runtime)
ENV FYERS_CLIENT_ID="YOUR_CLIENT_ID"
ENV FYERS_SECRET_KEY="YOUR_SECRET_KEY"
ENV FYERS_ACCESS_TOKEN=""
ENV EXECUTION_MODE="PAPER"

# Run main.py when the container launches
CMD ["python", "main.py"]
