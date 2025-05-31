# Use Python 3.8 image as base
FROM python:3.8-slim

# Set working directory inside the container
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt /app/

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . /app

# Environment variables for database credentials (can be overridden at runtime)
ENV DB_HOST=timescaledb
ENV DB_NAME=my_timescale_db
ENV DB_USER=postgres
ENV DB_PASSWORD=mysecretpassword
ENV BINANCE_API_KEY=your_api_key
ENV BINANCE_API_SECRET=your_api_secret
ENV LOG_LEVEL=INFO
ENV PYTHONUNBUFFERED=1

# Default command shows help - override with your desired arguments
CMD ["python", "app.py", "--help"]
