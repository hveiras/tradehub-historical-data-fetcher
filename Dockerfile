# Use Python 3.8 image as base
FROM python:3.8-slim

# Set working directory inside the container
WORKDIR /app

COPY . /app

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Environment variables for database credentials (can be overridden at runtime)
ENV DB_HOST=timescaledb
ENV DB_NAME=my_timescale_db
ENV DB_USER=postgres
ENV DB_PASSWORD=mysecretpassword
ENV API_KEY=your_api_key
ENV API_SECRET=your_api_secret

# Command to run the collector script
CMD ["python", "app.py"]
