#!/usr/bin/env bash
set -euo pipefail

# Verificador de seguridad antes de cada commit para evitar filtración de secretos.
echo "🔍 Verificando que no existan secretos ni sesiones en los archivos preparados para commit..."

STAGED_FILES=$(git diff --cached --name-only)

if [ -z "$STAGED_FILES" ]; then
  echo "ℹ️ No hay archivos en staging."
  exit 0
fi

# 1. Prohibir archivos prohibidos por nombre
for file in $STAGED_FILES; do
  case "$file" in
    .env|.env.local|.env.production|*.session|*.session-journal|*.db|*.sqlite|secrets/*)
      echo "❌ ERROR CRÍTICO: Archivo sensible detectado en staging: $file"
      exit 1
      ;;
  esac
done

# 2. Buscar patrones de valores asignados a variables críticas (excluyendo .env.example y este script)
FILTERED_FILES=$(echo "$STAGED_FILES" | grep -Ev '^(\.env\.example|backend/scripts/check_secrets\.sh)$' || true)

if [ -n "$FILTERED_FILES" ]; then
  if git diff --cached -- $FILTERED_FILES | grep -E '^\+.*(TELEGRAM_API_HASH|TELEGRAM_PHONE|ADMIN_PASSWORD|JWT_SECRET)\s*=\s*["'\'']?[A-Za-z0-9_+=-]{4,}' >/dev/null; then
    echo "❌ ERROR CRÍTICO: Posible credencial o secreto hardcodeado en el diff."
    exit 1
  fi
fi

echo "✅ Verificación de secretos superada: 0 secretos expuestos."
