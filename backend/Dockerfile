FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better Docker layer caching
COPY app/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/
COPY instance/ ./instance/

# Create instance directory if it doesn't exist
RUN mkdir -p instance

# Expose the port the app runs on
EXPOSE 5000

# Set environment variables
ENV FLASK_APP=app/app.py
ENV FLASK_ENV=development

# Run the application
CMD ["python", "app/app.py"]