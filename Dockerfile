# Dockerfile
FROM python:3.13-slim

# Arbeitsverzeichnis im Container festlegen
WORKDIR /app

# Systemabhängigkeiten und uv installieren
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && curl -LsSf https://astral.sh/uv/install.sh | sh \
    && rm -rf /var/lib/apt/lists/*

# Python-Abhängigkeiten kopieren und mit uv installieren
COPY requirements.txt .
RUN ~/.cargo/bin/uv pip install --system --no-cache -r requirements.txt

# Anwendungscode kopieren
COPY main.py .

# Datenverzeichnis erstellen
RUN mkdir -p /app/data

# Port freigeben
EXPOSE 8000

# Umgebungsvariablen setzen
ENV PYTHONUNBUFFERED=1

# Volumes für Datenpersistenz
VOLUME ["/app/data"]

# Anwendung starten
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]