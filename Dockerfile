FROM python:3.12-slim

WORKDIR /app

# Pre-cache requirements installation
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the minimal entrypoint (run.py), rest will come from volume
COPY run.py .

# Avoid buffering logs
ENV PYTHONUNBUFFERED=1

CMD ["python3", "run.py"]