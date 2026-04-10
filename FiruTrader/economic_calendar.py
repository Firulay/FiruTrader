import requests
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from urllib.parse import urljoin

try:
    import cloudscraper
except ImportError:
    cloudscraper = None


CALENDAR_URL = "https://www.investing.com/economic-calendar/"
FF_CALENDAR_URL = "https://nfs.faireconomy.media/ff_calendar_thisweek.xml"


def _clean(value):
    if value is None:
        return ""
    return " ".join(str(value).split()).strip()


def _first_text(node, selectors):
    for sel in selectors:
        el = node.select_one(sel)
        if el:
            txt = _clean(el.get_text(" ", strip=True))
            if txt:
                return txt
    return ""


def _impact_level(row):
    impact_td = row.select_one("td.sentiment, td.left.textNum.sentiment")
    if not impact_td:
        return 0

    icons = impact_td.select("i[data-img_key], i.grayFullBullishIcon, i.full")
    if not icons:
        return 0

    level = 0
    for icon in icons:
        key = (icon.get("data-img_key") or "").lower()
        classes = " ".join(icon.get("class", [])).lower()

        if "bull3" in key or "high" in classes:
            level = max(level, 3)
        elif "bull2" in key or "medium" in classes:
            level = max(level, 2)
        elif "bull1" in key or "low" in classes:
            level = max(level, 1)
        else:
            # fallback: contar iconos "filled"
            level = max(level, 1)

    return level


def _parse_ff_datetime(date_text, time_text):
    date_text = _clean(date_text)
    time_text = _clean(time_text)
    low_time = time_text.lower()

    if not date_text or not time_text:
        return None
    if "all day" in low_time or "tentative" in low_time:
        return None

    combined = f"{date_text} {time_text}"
    formats = (
        "%m-%d-%Y %I:%M%p",
        "%d-%m-%Y %I:%M%p",
    )

    for fmt in formats:
        try:
            # ForexFactory no expone TZ en este feed; usamos UTC para comparaciones consistentes.
            return datetime.strptime(combined, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue

    return None


def _is_cloudflare_block(html_text):
    low_html = (html_text or "").lower()
    markers = ("just a moment", "cf-chl", "captcha", "attention required")
    return any(marker in low_html for marker in markers)


def _calendar_headers():
    return {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.investing.com/",
    }


def _fetch_calendar_html():
    headers = _calendar_headers()

    # 1) Primer intento: cloudscraper para sortear challenge de Cloudflare.
    if cloudscraper is not None:
        try:
            scraper = cloudscraper.create_scraper(
                browser={"browser": "chrome", "platform": "windows", "mobile": False}
            )
            res = scraper.get(CALENDAR_URL, headers=headers, timeout=25)
            if res.status_code == 200 and not _is_cloudflare_block(res.text):
                print("📅 Calendario obtenido con cloudscraper")
                return res.text
            print(f"⚠️ cloudscraper sin datos utiles (HTTP {res.status_code})")
        except requests.RequestException as exc:
            print(f"⚠️ cloudscraper fallo por red: {exc}")
        except Exception as exc:
            print(f"⚠️ cloudscraper fallo: {exc}")

    # 2) Fallback: requests normal.
    try:
        res = requests.get(CALENDAR_URL, headers=headers, timeout=25)
    except requests.RequestException as exc:
        print(f"⚠️ Calendario no disponible (red): {exc}")
        return ""

    if res.status_code != 200:
        print(f"⚠️ Calendario no disponible (HTTP {res.status_code})")
        return ""

    if _is_cloudflare_block(res.text):
        print("⚠️ Calendario bloqueado por anti-bot (Cloudflare/CAPTCHA)")
        return ""

    print("📅 Calendario obtenido con requests")
    return res.text


def _parse_forex_factory_events(xml_text):
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        print("⚠️ Fallback FF no disponible (XML invalido)")
        return []

    events = []

    for item in root.findall(".//event"):
        country = _clean(item.findtext("country")).lower()
        if country not in {"usd", "united states"}:
            continue

        impact = _clean(item.findtext("impact")).lower()
        if impact not in {"high", "medium"}:
            continue

        title = _clean(item.findtext("title"))
        if not title:
            continue

        date = _clean(item.findtext("date"))
        time_event = _clean(item.findtext("time"))
        actual = _clean(item.findtext("actual"))
        forecast = _clean(item.findtext("forecast"))
        previous = _clean(item.findtext("previous"))
        event_url = _clean(item.findtext("url")) or "https://www.forexfactory.com/calendar"
        event_dt = _parse_ff_datetime(date, time_event)

        event_id = f"ff-{date}-{time_event}-{title}".lower()

        events.append(
            {
                "id": event_id,
                "title": title,
                "time": f"{date} {time_event}".strip() or "-",
                "actual": actual,
                "forecast": forecast,
                "previous": previous,
                "source_name": "ForexFactory",
                "source_url": "https://www.forexfactory.com/calendar",
                "event_url": event_url,
                "event_datetime": event_dt.isoformat() if event_dt else "",
            }
        )

    return events


def _get_ff_us_events():
    try:
        response = requests.get(FF_CALENDAR_URL, timeout=20)
    except requests.RequestException as exc:
        print(f"⚠️ Fallback FF no disponible (red): {exc}")
        return []

    if response.status_code != 200:
        print(f"⚠️ Fallback FF no disponible (HTTP {response.status_code})")
        return []

    events = _parse_forex_factory_events(response.text)
    if events:
        print(f"📅 Calendario obtenido desde fallback FF: {len(events)} eventos")
    else:
        print("⚠️ Fallback FF activo pero sin eventos utiles")
    return events


def get_us_events():
    html = _fetch_calendar_html()
    if not html:
        return _get_ff_us_events()

    soup = BeautifulSoup(html, "html.parser")

    row_selectors = [
        "tr.js-event-item",
        "tr[id^='eventRowId_']",
        "tr[data-event-id]",
        "table#economicCalendarData tr",
    ]

    rows = []
    for sel in row_selectors:
        rows = soup.select(sel)
        if rows:
            break

    if not rows:
        print("⚠️ Calendario no disponible (sin filas de eventos)")
        return _get_ff_us_events()

    events = []

    for row in rows:
        event_id = (row.get("data-event-id") or "").strip()
        if not event_id:
            rid = (row.get("id") or "").strip()
            if rid.startswith("eventRowId_"):
                event_id = rid.replace("eventRowId_", "").strip()

        event_url = CALENDAR_URL
        event_anchor = row.select_one("td.event a")
        if event_anchor and event_anchor.get("href"):
            event_url = urljoin("https://www.investing.com", event_anchor.get("href"))

        title = _first_text(row, ["td.event", "td.left.event", "td.event a", "a.event"])
        if not title:
            continue

        country_text = _first_text(
            row,
            [
                "td.flagCur",
                "td.flagCur span[title]",
                "td.left.flagCur.noWrap",
            ],
        ).lower()

        # Solo eventos USA/USD para evitar ruido.
        if "united states" not in country_text and "usd" not in country_text:
            continue

        impact = _impact_level(row)
        if impact < 2:
            continue

        time_event = _first_text(row, ["td.time", "td.first.left.time"]) or "-"
        actual = _first_text(row, ["td.actual", "td.act"])
        forecast = _first_text(row, ["td.forecast", "td.fore", "td.for"])
        previous = _first_text(row, ["td.previous", "td.prev"])

        if not event_id:
            event_id = f"{title}-{time_event}"

        events.append(
            {
                "id": event_id,
                "title": title,
                "time": time_event,
                "actual": actual,
                "forecast": forecast,
                "previous": previous,
                "source_name": "Investing",
                "source_url": CALENDAR_URL,
                "event_url": event_url,
                "event_datetime": "",
            }
        )

    if events:
        return events

    print("⚠️ Investing no devolvio eventos utiles; activando fallback FF")
    return _get_ff_us_events()

