#!/bin/bash
# ═══════════════════════════════════════════════
#  start.sh — Arranca Flask + Celery + Redis
# ═══════════════════════════════════════════════

source venv/bin/activate
export FLASK_APP=app.py

# Matar procesos anteriores si los hay
pkill -f "celery worker" 2>/dev/null || true
pkill -f "gunicorn"      2>/dev/null || true

mkdir -p logs

echo "🔴 Verificando Redis..."
redis-cli ping | grep -q PONG && echo "✅ Redis OK" || { echo "❌ Redis no responde. Inicia: sudo systemctl start redis"; exit 1; }

echo "⚙️  Iniciando Celery workers (4 concurrentes)..."
celery -A tareas.celery worker \
    --concurrency=4 \
    --loglevel=info \
    --logfile=logs/celery.log \
    --detach
echo "✅ Celery iniciado (logs/celery.log)"

echo "🌐 Iniciando Flask con Gunicorn + eventlet..."
gunicorn \
    --worker-class eventlet \
    --workers 1 \
    --bind 0.0.0.0:5000 \
    --timeout 300 \
    --access-logfile logs/access.log \
    --error-logfile logs/error.log \
    "app:app" &

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║  ✅ Sistema iniciado                      ║"
echo "║  🌐 URL: http://$(hostname -I | awk '{print $1}'):5000  ║"
echo "║  👤 Admin: admin / Admin123!              ║"
echo "║                                          ║"
echo "║  Logs:  tail -f logs/celery.log           ║"
echo "║         tail -f logs/error.log            ║"
echo "╚══════════════════════════════════════════╝"
