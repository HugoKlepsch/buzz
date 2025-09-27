# Simple Dockerfile for buzz.py
# Uses minimal Python 3 Alpine image for smallest footprint
FROM python:3-alpine

# Create app directory
WORKDIR /app

# Copy the application file
COPY buzz.py /app/buzz.py

# Expose the application port
EXPOSE 8080

# Run the server
CMD ["python", "/app/buzz.py"]
