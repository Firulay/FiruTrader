# FiruTrader

Bot de noticias macro para oro con envio a Telegram.

## Requisitos

- Python 3.11+
- Dependencias en `requirements.txt`

## Ejecucion local

1. Crea y activa entorno virtual.
2. Instala dependencias.
3. Copia `.env.example` a `.env` y completa valores.
4. Ejecuta el bot.

## Variables de entorno

- `TELEGRAM_TOKEN` (requerida)
- `CHAT_IDS` (requerida, CSV: `id1,id2`)
- `RSS_URLS` (opcional, CSV)
- `CHECK_INTERVAL` (opcional, segundos)
- `TEST_MODE` (opcional: `true/false`)
- `SENT_FILE_PATH` (opcional, recomendado en Railway)
- `DATA_DIR` (opcional, alternativa a `SENT_FILE_PATH`)

## Deploy en Railway (Worker)

1. Sube el repo a GitHub.
2. En Railway, crea proyecto desde ese repo.
3. Configura el servicio como **Worker**.
4. Start Command: `python main.py`.
5. Agrega variables de entorno desde `.env.example` (recomendado `CHECK_INTERVAL=60`).
6. Crea un **Volume** en Railway y montalo en `/data`.
7. Define `SENT_FILE_PATH=/data/sent.json` para persistir duplicados entre reinicios.

## Notas

- `sent.json` evita duplicados entre ciclos.
- Sin volumen persistente, los duplicados pueden reaparecer tras reinicios.
- El calendario economico intenta Investing primero; si Cloudflare bloquea, usa fallback XML de ForexFactory automaticamente.
- Si existe un evento con fecha/hora parseable en los proximos 60 minutos, el bot envia una alerta previa adicional.
