import os


def _parse_csv(value):
    return [item.strip() for item in value.split(",") if item.strip()]


def _parse_bool(value, default=False):
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "").strip()
CHAT_IDS = _parse_csv(os.getenv("CHAT_IDS", ""))

if not TELEGRAM_TOKEN:
    raise ValueError("Falta variable de entorno TELEGRAM_TOKEN")
if not CHAT_IDS:
    raise ValueError("Falta variable de entorno CHAT_IDS (CSV)")

_default_rss = [
    "https://www.investing.com/rss/news_25.rss",
    "https://www.cnbc.com/id/10000664/device/rss/rss.html",
    "https://feeds.content.dowjones.io/public/rss/mw_topstories",
    "https://www.fxstreet.com/rss/news",
    "https://www.federalreserve.gov/feeds/press_all.xml",
    "https://www.ecb.europa.eu/press/rss/press.html",
]
RSS_URLS = _parse_csv(os.getenv("RSS_URLS", ",".join(_default_rss)))

CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "60"))
TEST_MODE = _parse_bool(os.getenv("TEST_MODE"), default=False)

# 🎯 Control de ruido
TOP_NEWS_PER_CYCLE = 3
MIN_GOLD_SCORE = 5
MIN_MACRO_SCORE = 7
MIN_FINAL_SCORE_TO_SEND = 7
BURST_MIN_COUNT = 2
BURST_BONUS_PER_KEYWORD = 1
MAX_BURST_BONUS = 3
