FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive
WORKDIR /app

# ── Dependencias del sistema + Google Chrome ──
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl wget ca-certificates gnupg2 unzip \
    libglib2.0-0 libnss3 libfontconfig1 \
    libx11-6 libx11-xcb1 libxcb1 libxcomposite1 libxcursor1 \
    libxdamage1 libxext6 libxfixes3 libxi6 libxrandr2 \
    libxrender1 libxss1 libxtst6 fonts-liberation \
    libasound2 libatk-bridge2.0-0 libatk1.0-0 \
    libcups2 libdbus-1-3 libdrm2 libgbm1 libgtk-3-0 libnspr4 \
    default-mysql-client \
    && wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
    && apt-get install -y ./google-chrome-stable_current_amd64.deb \
    && rm google-chrome-stable_current_amd64.deb \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# ── Dependencias Python ──
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# ── Código fuente ──
COPY . .

# ── Carpetas de trabajo ──
RUN mkdir -p uploads outputs logs

EXPOSE 5000
CMD ["gunicorn", \
     "--worker-class", "eventlet", \
     "--workers", "1", \
     "--bind", "0.0.0.0:5000", \
     "--timeout", "300", \
     "--access-logfile", "logs/access.log", \
     "--error-logfile", "logs/error.log", \
     "app:app"]
