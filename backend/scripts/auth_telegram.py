#!/usr/bin/env python3
"""
Script interactivo de autenticación de Telegram (Telethon MTProto).
Genera el archivo .session en la ruta definida por TELEGRAM_SESSION_PATH (fuera del repositorio).
Modo estrictamente solo lectura: nunca envía mensajes.
"""
import asyncio
import os
import sys
from pathlib import Path

# Añadir el directorio backend al path
BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
from app.config import settings


async def main():
    if not settings.is_telegram_configured:
        print("❌ Error: Configura TELEGRAM_API_ID, TELEGRAM_API_HASH y TELEGRAM_PHONE en tu archivo .env")
        sys.exit(1)

    session_path = Path(settings.TELEGRAM_SESSION_PATH)
    session_path.parent.mkdir(parents=True, exist_ok=True)
    # Restringir permisos de la carpeta de secretos
    try:
        os.chmod(session_path.parent, 0o700)
    except OSError:
        pass

    print(f"🔐 Iniciando autenticación MTProto (Modo Solo Lectura)...")
    print(f"📁 El archivo de sesión se guardará fuera de Git en: {session_path}.session")

    client = TelegramClient(
        str(session_path),
        int(settings.TELEGRAM_API_ID),
        settings.TELEGRAM_API_HASH,
    )

    await client.connect()
    if not await client.is_user_authorized():
        print("📲 Enviando solicitud de código a tu cuenta de Telegram...")
        await client.send_code_request(settings.TELEGRAM_PHONE)
        code = input("👉 Introduce el código de verificación recibido en Telegram: ").strip()
        try:
            await client.sign_in(settings.TELEGRAM_PHONE, code)
        except SessionPasswordNeededError:
            import getpass
            pw = getpass.getpass("🔒 Cuenta con 2FA activo. Introduce tu contraseña de Telegram: ")
            await client.sign_in(password=pw)

    me = await client.get_me()
    session_file = session_path if session_path.suffix == ".session" else session_path.with_suffix(".session")
    if session_file.exists():
        os.chmod(session_file, 0o600)

    print(f"✅ Sesión iniciada correctamente como @{getattr(me, 'username', 'usuario')} (ID: {me.id}).")
    print("🔒 Permisos 600 aplicados al archivo de sesión.")
    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
