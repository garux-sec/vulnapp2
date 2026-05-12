FROM python:3.9-slim

WORKDIR /app

# VULNERABLE: No non-root user — runs as root
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .

EXPOSE 8000

# VULNERABLE: debug mode + reload exposed
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
