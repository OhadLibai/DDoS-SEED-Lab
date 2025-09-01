# HTTP/2 Victim Server (Multi-purpose: Single-worker or Multi-worker)
FROM python:3.10
WORKDIR /app
COPY victim_app.py .
COPY scenarios/ ./scenarios/
COPY requirements.txt .
RUN pip install -r requirements.txt

# Server starts based on environment configuration
CMD ["python", "-u", "victim_app.py"]