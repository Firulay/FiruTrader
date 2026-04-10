import feedparser


def get_news(rss_urls):
    """
    Obtiene noticias desde una o varias fuentes RSS.
    Retorna una lista de dicts con: title, link, source.
    """
    if isinstance(rss_urls, str):
        rss_urls = [rss_urls]

    entries = []
    seen = set()

    for rss_url in rss_urls:
        try:
            feed = feedparser.parse(rss_url)
        except Exception as exc:
            print(f"⚠️ Error leyendo RSS {rss_url}: {exc}")
            continue

        for item in feed.entries:
            title = getattr(item, "title", "").strip()
            link = getattr(item, "link", "").strip()

            if not title:
                continue

            # Prioriza el link para deduplicar; usa título como fallback.
            dedupe_key = link or title.lower()
            if dedupe_key in seen:
                continue

            seen.add(dedupe_key)
            entries.append(
                {
                    "title": title,
                    "link": link or f"no-link://{title}",
                    "source": rss_url,
                }
            )

    return entries
