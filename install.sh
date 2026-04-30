#!/bin/bash
# ═══════════════════════════════════════════════════════
#  INSTALACIÓN COMPLETA - Agendamiento WFM Claro
#  Servidor Linux (Ubuntu 20.04 / 22.04)
# ═══════════════════════════════════════════════════════

set -e

echo ""
echo "╔══════════════════════════════════════╗"
echo "║  Instalando Agendamiento WFM Claro   ║"
echo "╚══════════════════════════════════════╝"
echo ""

# ── 1. Dependencias del sistema ──
echo "📦 Instalando dependencias del sistema..."
sudo apt-get update -q
sudo apt-get install -y -q \
    python3 python3-pip python3-venv \
    redis-server \
    wget curl unzip \
    libmysqlclient-dev \
    pkg-config

# ── 2. Chrome headless ──
echo "🌐 Instalando Google Chrome..."
if ! command -v google-chrome &>/dev/null; then
    wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
    sudo apt-get install -y -q ./google-chrome-stable_current_amd64.deb
    rm google-chrome-stable_current_amd64.deb
    echo "✅ Chrome instalado: $(google-chrome --version)"
else
    echo "✅ Chrome ya instalado: $(google-chrome --version)"
fi

# ── 3. Entorno virtual Python ──
echo "🐍 Creando entorno virtual Python..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q
echo "✅ Dependencias Python instaladas."

# ── 4. Redis ──
echo "🔴 Iniciando Redis..."
sudo systemctl enable redis-server
sudo systemctl start redis-server
echo "✅ Redis corriendo."

# ── 5. Base de datos MySQL ──
echo ""
echo "🗄️  CONFIGURACIÓN MYSQL"
echo "   Edita config.py con tus credenciales MySQL antes de continuar."
echo "   Luego ejecuta: flask init-db"
echo ""

echo "✅ Instalación base completada."
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  PASOS SIGUIENTES:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  1. Edita config.py con tus datos de MySQL"
echo "  2. source venv/bin/activate"
echo "  3. flask init-db"
echo "  4. bash start.sh"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
