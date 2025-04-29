# Use official Python image with slim base
FROM python:3.11-slim

# Install system packages required by dlib and face_recognition
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    libopenblas-dev \
    liblapack-dev \
    libx11-dev \
    libgtk-3-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy all files to the container
COPY . /app

# Upgrade pip and install Python dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Expose the port your Flask app runs on
EXPOSE 5000

# Command to run the Flask app
CMD ["python", "app.py"]
