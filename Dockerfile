# Use a Python base image
FROM python:3.10-slim

# Install system dependencies, including ffmpeg and Myanmar fonts
RUN apt-get update && apt-get install -y \
    ffmpeg \
    fonts-noto-myanmar \
    && rm -rf /var/lib/apt/lists/*

# Set up working directory
WORKDIR /app

# Copy dependency specifications
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy codebase
COPY . .

# Run entrypoint script (supports topic override as argument)
ENTRYPOINT ["python", "main.py"]
