# HTTP/2 Victim Server (Multi-purpose: Single-worker or Multi-worker)
FROM python:3.10
WORKDIR /app

# Copy application and scenario files
COPY victim_app.py .
COPY scenarios/ ./scenarios/
COPY requirements.txt .

# Copy the new entrypoint script
COPY entrypoint.sh .

# Install dependencies
RUN pip install -r requirements.txt && chmod +x entrypoint.sh

# The server is started by the entrypoint script based on environment configuration.
CMD ["./entrypoint.sh"]