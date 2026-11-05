# Gold Signals (`/gold`)

Aplicación full-stack en **modo estrictamente solo lectura** para capturar señales de trading de oro (`XAUUSD` y futuros `GC`) publicadas en canales de Telegram (comenzando por `@tagsignals`), evaluarlas automáticamente frente al precio real posterior y mostrar su desempeño en un tablero web protegido bajo `https://desarrollaunbyte.com/gold/`.

> **Aviso importante**: Esta herramienta es únicamente un registro estadístico en **modo solo lectura**. La aplicación nunca envía mensajes, nunca ejecuta órdenes, nunca se conecta a brókers y nunca toca dinero. **No es asesoría financiera.**

---

## Arquitectura

- **Lector de Telegram (`backend/app/listener.py`)**: Cliente de usuario MTProto con **Telethon** en modo solo lectura (`iter_messages` + `events.NewMessage`).
- **Parser de Señales (`backend/app/parser.py`)**: Extrae dirección (`COMPRA`/`VENTA`), instrumento (`XAUUSD`/`GC`), precio o rango de entrada, `Stop Loss (SL)` y múltiples `Take Profits (TP1..TP4)` desde formatos variables y texto libre. Si un mensaje no contiene datos suficientes o es informativo, se guarda como **`SIN_INTERPRETAR`** sin inventar valores.
- **Evaluador (`backend/app/evaluator.py`)**: Consulta velas históricas OHLC reales posteriores al mensaje desde fuentes públicas (Yahoo Finance API para `GC=F` y `XAUUSD=X`) y determina si la señal está `PENDIENTE`, `GANADA`, `PERDIDA`, `EXPIRADA` o `NO_DISPONIBLE`, calculando pips ($1\text{ pip} = 0.10\text{ USD}$), porcentaje y tiempo hasta objetivo o stop.
- **Backend API (`backend/app/main.py`)**: **FastAPI + SQLite (modo WAL)** con autenticación mediante usuario/contraseña en variables de entorno y cookie/token JWT.
- **Tablero Web (`frontend/`)**: **React + TypeScript + Vite + Tailwind CSS**, compilado con `base: '/gold/'` para funcionar en subcarpeta detrás de Nginx.

---

## Seguridad y Variables de Entorno

Ningún secreto, número de teléfono ni sesión de Telegram se guarda en el código ni en Git:

1. Copia `.env.example` a `.env` (excluido por `.gitignore`):
   ```bash
   cp .env.example .env
   chmod 600 .env
   ```
2. Rellena las variables:
   - `ADMIN_USERNAME` y `ADMIN_PASSWORD`: credenciales para iniciar sesión en el tablero web.
   - `JWT_SECRET`: cadena aleatoria segura (`openssl rand -hex 32`).
   - `TELEGRAM_API_ID`, `TELEGRAM_API_HASH`, `TELEGRAM_PHONE`: credenciales de https://my.telegram.org.
   - `TELEGRAM_SESSION_PATH`: ruta fuera del repositorio (ej. `/var/lib/gold-signals/telegram_gold` en el VPS o `./secrets/telegram_gold` en local).

Antes de cada commit se ejecuta:
```bash
bash backend/scripts/check_secrets.sh
```

---

## Ejecución Local (Desarrollo y Preview)

### 1. Backend
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Poblar datos de ejemplo claramente etiquetados como [EJEMPLO]
python -m app.seed_demo

# Iniciar servidor en http://127.0.0.1:8010/gold/
uvicorn app.main:app --reload --port 8010
```

### 2. Frontend
```bash
cd frontend
npm install
npm run build
```
*(El backend FastAPI sirve automáticamente el bundle compilado de `frontend/dist` en `http://127.0.0.1:8010/gold/`, o puedes usar `npm run dev` en el puerto 5173 con proxy a `:8010`).*

---

## Autenticación y Lector de Telegram (Telethon)

Para iniciar sesión en Telegram por primera vez (genera el archivo `.session` fuera del repo):
```bash
cd backend
source .venv/bin/activate
python scripts/auth_telegram.py
```
El script solicitará por consola el código enviado a tu cuenta de Telegram y, si tienes verificación en dos pasos (2FA), tu contraseña.

Para correr el lector y evaluador continuo:
```bash
python -m app.listener
```

### Cómo revocar la sesión de Telegram
Si en cualquier momento deseas desconectar la aplicación de tu cuenta de Telegram:
1. Abre la app oficial de **Telegram** en tu teléfono o escritorio.
2. Ve a **Ajustes (Settings) → Dispositivos (Devices)**.
3. Busca la sesión activa correspondiente a `Gold Signals / Telethon` y pulsa **Cerrar sesión (Terminate Session)**.
4. En el servidor VPS, detén el servicio y elimina el archivo `.session`:
   ```bash
   sudo systemctl stop gold-listener
   sudo rm -f /var/lib/gold-signals/*.session*
   ```

---

## Despliegue en VPS Hostinger (`/var/www/gold`)

Consulta `deploy/deploy.sh`, `deploy/gold-web.service`, `deploy/gold-listener.service` y `deploy/nginx-gold.conf` para la configuración completa en producción bajo `https://desarrollaunbyte.com/gold/`.
