# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PORT 8080

# Set the working directory in the container
WORKDIR /app

# Install system dependencies (libgomp1 is critical for torch/scvi on Linux)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install CPU-only version of PyTorch first to reduce image size
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container at /app
COPY . .

# Expose the port the app runs on (Railway will override this)
EXPOSE 8080

# Command to run the application
# We use uvicorn directly to ensure it handles the PORT environment variable
CMD uvicorn bridge_server:app --host 0.0.0.0 --port ${PORT}
