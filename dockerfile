# Use official Python image
FROM python:3.11-slim

# Set working directory inside container
WORKDIR /app

# Copy requirements and install
COPY . .
RUN pip install --no-cache-dir -r scripts/requirements.txt

# Expose the port Dash will run on
EXPOSE 8050

# Set default command
CMD ["python", "scripts/dashboard.py"]
