import time
from datetime import datetime, timezone

from config import TELEGRAM_TOKEN, CHAT_IDS, RSS_URLS, CHECK_INTERVAL, TEST_MODE
from economic_calendar import get_us_events
from rss import get_news
from scorer import calculate_score, classify
from filter import is_relevant
from storage import load_sent, save_sent
from translator import translate
from telegram_sender import send_message
from test_data import get_test_news

ALERT_WINDOW_MINUTES = 60


def build_news_message(title, title_es, score, link, impact):
    """
    Construye el mensaje final para Telegram
    """
    return f"""{impact}

📰 {title_es}

🇺🇸 {title}

📊 Score: {score}

🔗 {link}
"""


def build_calendar_message(title, title_es, time_event, actual, forecast, previous, link, source_name):
    """
    Construye el mensaje para eventos del calendario económico.
    """
    return f"""📅 EVENTO ECONÓMICO (USA)

📰 {title_es}

🇺🇸 {title}

⏰ {time_event}

📊 Actual: {actual or "-"} | Prev: {forecast or "-"} | Ant: {previous or "-"}

🛰️ Fuente: {source_name}

🔗 {link}
"""


def build_upcoming_event_message(title, title_es, time_event, minutes_left, link, source_name):
    return f"""⏰ PRÓXIMO EVENTO ECONÓMICO (<= 60 min)

📰 {title_es}

🇺🇸 {title}

⌛ Faltan aprox: {minutes_left} min
⏰ Hora: {time_event}

🛰️ Fuente: {source_name}
🔗 {link}
"""


def _parse_event_datetime(event):
    value = (event.get("event_datetime") or "").strip()
    if not value:
        return None

    try:
        dt = datetime.fromisoformat(value)
    except ValueError:
        return None

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    return dt


def _find_upcoming_event(events, window_minutes):
    now_utc = datetime.now(timezone.utc)
    best = None
    best_minutes = None

    for event in events:
        event_dt = _parse_event_datetime(event)
        if not event_dt:
            continue

        delta_minutes = int((event_dt - now_utc).total_seconds() // 60)
        if delta_minutes < 0 or delta_minutes > window_minutes:
            continue

        if best_minutes is None or delta_minutes < best_minutes:
            best = event
            best_minutes = delta_minutes

    if best is None:
        return None, None

    return best, best_minutes

def run():

    print("🚀 FiruBot iniciado...\n")

    sent = load_sent()

    while True:
        try:
            # =========================
            # 📰 NOTICIAS
            # =========================
            # 🔁 Elegir fuente (test o real)
            if TEST_MODE:
                news_list = get_test_news()
            else:
                news_list = get_news(RSS_URLS)

            for entry in news_list:
                title = entry.get("title", "").strip()
                link = entry.get("link", "").strip()
                source = entry.get("source", "test")

                if not title or not link:
                    continue

                content = title.lower()

                print(f"\n🧪 Procesando: {title}")
                print(f"🛰️ Fuente: {source}")

                score = calculate_score(content)
                print(f"📊 Score: {score}")

                # 🧹 Filtro relevancia
                if not is_relevant(content, score):
                    print("⛔ No relevante")
                    continue

                # 📊 Clasificación impacto
                impact = classify(score)
                if not impact:
                    print("⛔ Impacto bajo")
                    continue

                # 🚫 Evitar duplicados
                if link in sent:
                    print("⛔ Ya enviado")
                    continue

                # 🌍 Traducción
                title_es = translate(title)

                # 📨 Construir mensaje
                message = build_news_message(
                    title,
                    title_es,
                    score,
                    link,
                    impact
                )

                print("📨 Enviando noticia...")

                delivered = False
                for chat_id in CHAT_IDS:
                    if send_message(TELEGRAM_TOKEN, chat_id, message):
                        delivered = True

                if delivered:
                    sent.add(link)
                else:
                    print("⚠️ No se guarda como enviada porque fallo en todos los chats")

            # =========================
            # 📅 CALENDARIO ECONÓMICO
            # =========================
            try:
                events = get_us_events()
            except Exception as calendar_exc:
                print(f"⚠️ Error leyendo calendario económico: {calendar_exc}")
                events = []

            upcoming_event, minutes_left = _find_upcoming_event(events, ALERT_WINDOW_MINUTES)
            if upcoming_event is not None:
                alert_event_id = upcoming_event.get("id")
                if alert_event_id:
                    alert_sent_key = f"calendar_alert_{alert_event_id}"
                    if alert_sent_key not in sent:
                        alert_title = (upcoming_event.get("title") or "").strip()
                        alert_time = (upcoming_event.get("time") or "-").strip()
                        alert_link = (upcoming_event.get("event_url") or upcoming_event.get("source_url") or "https://www.forexfactory.com/calendar").strip()
                        alert_source = (upcoming_event.get("source_name") or "Calendario económico").strip()

                        if alert_title:
                            alert_title_es = translate(alert_title)
                            alert_message = build_upcoming_event_message(
                                alert_title,
                                alert_title_es,
                                alert_time,
                                minutes_left,
                                alert_link,
                                alert_source,
                            )

                            print(f"⏰ Enviando alerta próximo evento (faltan {minutes_left} min)...")
                            delivered = False
                            for chat_id in CHAT_IDS:
                                if send_message(TELEGRAM_TOKEN, chat_id, alert_message):
                                    delivered = True

                            if delivered:
                                sent.add(alert_sent_key)

            for event in events:
                event_id = event.get("id")
                title = (event.get("title") or "").strip()
                time_event = (event.get("time") or "-").strip()

                if not event_id or not title:
                    continue

                # ID único para evitar duplicados.
                sent_key = f"calendar_{event_id}"
                if sent_key in sent:
                    continue

                print(f"\n📅 Procesando evento: {title}")

                actual = (event.get("actual") or "").strip()
                forecast = (event.get("forecast") or "").strip()
                previous = (event.get("previous") or "").strip()
                event_link = (event.get("event_url") or event.get("source_url") or "https://www.investing.com/economic-calendar/").strip()
                source_name = (event.get("source_name") or "Calendario económico").strip()

                # Evita ruido de eventos sin cifras útiles.
                if not actual and not forecast:
                    print("⛔ Evento sin datos útiles")
                    continue

                # 🌍 Traducción
                title_es = translate(title)

                # 📨 Construir mensaje
                message = build_calendar_message(
                    title,
                    title_es,
                    time_event,
                    actual,
                    forecast,
                    previous,
                    event_link,
                    source_name,
                )

                print("📨 Enviando evento económico...")

                delivered = False
                for chat_id in CHAT_IDS:
                    if send_message(TELEGRAM_TOKEN, chat_id, message):
                        delivered = True

                if delivered:
                    sent.add(sent_key)
                else:
                    print("⚠️ No se guarda evento porque fallo en todos los chats")

            save_sent(sent)

        except Exception as e:
            print("❌ Error:", e)

        # ⏱️ Esperar siguiente ciclo
        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    try:
        run()
    except KeyboardInterrupt:
        print("\n🛑 FiruBot detenido por el usuario")
