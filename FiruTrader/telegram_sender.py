import requests


def send_message(token, chat_id, text):
    """
    Envía mensaje a Telegram y devuelve True si Telegram lo acepta.
    """
    url = f"https://api.telegram.org/bot{token}/sendMessage"

    payload = {
        "chat_id": chat_id,
        "text": text,
    }

    try:
        response = requests.post(url, data=payload, timeout=15)
    except requests.RequestException as exc:
        print(f"❌ Error de red al enviar a {chat_id}: {exc}")
        return False

    try:
        body = response.json()
    except ValueError:
        body = {}

    if response.status_code == 200 and body.get("ok"):
        print(f"📤 Enviado a {chat_id}: 200")
        return True

    description = body.get("description", "sin detalle")
    print(f"❌ Fallo envío a {chat_id}: {response.status_code} - {description}")
    return False
