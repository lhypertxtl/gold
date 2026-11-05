#!/usr/bin/env bash
set -euo pipefail

# ============================================================================
# Script idempotente de despliegue para Gold Signals en VPS Hostinger
# Ruta de instalación: /var/www/gold
# Ruta de datos y sesión fuera del repo: /var/lib/gold-signals
# ============================================================================

APP_DIR="/var/www/gold"
DATA_DIR="/var/lib/gold-signals"
SERVICE_USER="www-data"

echo "🚀 Iniciando despliegue de Gold Signals en ${APP_DIR}..."

# 1. Crear directorios de datos y secretos fuera del repositorio
sudo mkdir -p "${DATA_DIR}/secrets"
sudo chown -R "${SERVICE_USER}:${SERVICE_USER}" "${DATA_DIR}"
sudo chmod 700 "${DATA_DIR}/secrets"

# 2. Actualizar código desde Git (rama main)
if [ -d "${APP_DIR}/.git" ]; then
  echo "📥 Actualizando repositorio Git en ${APP_DIR}..."
  cd "${APP_DIR}"
  sudo -u "${SERVICE_USER}" git fetch origin main
  sudo -u "${SERVICE_USER}" git reset --hard origin/main
fi

# 3. Verificar archivo .env
if [ ! -f "${APP_DIR}/.env" ]; then
  echo "⚠️ No existe ${APP_DIR}/.env. Copiando plantilla .env.example..."
  sudo cp "${APP_DIR}/.env.example" "${APP_DIR}/.env"
  sudo chown "${SERVICE_USER}:${SERVICE_USER}" "${APP_DIR}/.env"
  sudo chmod 600 "${APP_DIR}/.env"
  echo "❗ Edita ${APP_DIR}/.env con las credenciales reales antes de iniciar los servicios."
fi

# 4. Configurar entorno virtual Python y dependencias del backend
echo "🐍 Instalando dependencias de Python..."
cd "${APP_DIR}/backend"
if [ ! -d ".venv" ]; then
  sudo -u "${SERVICE_USER}" python3 -m venv .venv
fi
sudo -u "${SERVICE_USER}" .venv/bin/pip install --upgrade pip
sudo -u "${SERVICE_USER}" .venv/bin/pip install -r requirements.txt

# 5. Compilar el frontend con base /gold/
echo "⚛️ Compilando frontend React (Vite base=/gold/)..."
cd "${APP_DIR}/frontend"
sudo -u "${SERVICE_USER}" npm install
sudo -u "${SERVICE_USER}" npm run build

# 6. Instalar y recargar servicios systemd
echo "⚙️ Configurando unidades systemd (gold-web y gold-listener)..."
sudo cp "${APP_DIR}/deploy/gold-web.service" /etc/systemd/system/gold-web.service
sudo cp "${APP_DIR}/deploy/gold-listener.service" /etc/systemd/system/gold-listener.service
sudo systemctl daemon-reload
sudo systemctl enable gold-web.service
sudo systemctl restart gold-web.service

# Solo iniciar gold-listener si el archivo .session ya existe
if ls "${DATA_DIR}/secrets/"*.session >/dev/null 2>&1; then
  sudo systemctl enable gold-listener.service
  sudo systemctl restart gold-listener.service
  echo "✅ Servicio gold-listener reiniciado."
else
  echo "ℹ️ Aún no hay archivo .session en ${DATA_DIR}/secrets/. Ejecuta scripts/auth_telegram.py para activarlo."
fi

# 7. Validar configuración de Nginx y recargar
echo "🌐 Verificando configuración de Nginx..."
sudo nginx -t
sudo systemctl reload nginx

echo "✅ Despliegue completado con éxito. Disponible en https://desarrollaunbyte.com/gold/"
