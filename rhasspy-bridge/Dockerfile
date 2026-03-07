FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates curl gnupg \
    && rm -rf /var/lib/apt/lists/*

# Install OpenClaw CLI for Telegram forwarding via bridge
RUN npm install -g openclaw

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY bridge.py .

EXPOSE 8099

CMD ["python", "bridge.py"]
