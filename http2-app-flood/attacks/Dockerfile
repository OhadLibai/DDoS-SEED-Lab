# HTTP/2 Attack Client
FROM python:3.10
WORKDIR /app
COPY http2_flood.py .
COPY cloud_http2_flood.py .
COPY requirements.txt .
RUN pip install -r requirements.txt

# Default command - can be overridden in docker-compose
CMD ["python", "http2_flood.py"]