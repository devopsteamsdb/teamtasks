# Use latest official Python slim image
FROM python:3-slim

# Set the working directory in the container
WORKDIR /app

# Install curl for container health check
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements first for optimized Docker layer caching
COPY requirements.txt /app/

# Upgrade pip and install dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application files
COPY . /app

# Create uploads directory for persistent storage
RUN mkdir -p /app/uploads/avatars && \
    mkdir -p /app/instance

# Expose port 5000
EXPOSE 5000

# Modern Flask and Python environment variables
ENV FLASK_APP=app.py
ENV FLASK_DEBUG=0
ENV PYTHONUNBUFFERED=1

# Run with Gunicorn WSGI production server
# Use 2 workers with 16 threads each (32 concurrent request threads) so slow AI calls,
# SSE streams, or parallel asset fetches never starve Chrome HTTP/1.1 Keep-Alive sockets.
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--threads", "16", "--timeout", "120", "--graceful-timeout", "30", "--keep-alive", "5", "--error-logfile", "-", "app:app"]
