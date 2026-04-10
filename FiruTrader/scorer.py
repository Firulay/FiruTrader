# Listas de palabras clave agrupadas por impacto

GOLD = ["gold", "xau", "bullion", "precious metals"]
FED = ["fed", "federal reserve", "fomc", "powell", "rate", "interest"]
INFLATION = ["inflation", "cpi", "ppi", "recession", "gdp"]
DOLLAR = ["usd", "dollar", "dxy"]
GEO = ["war", "conflict", "geopolitical", "crisis"]
FINANCIAL = ["bank", "liquidity", "credit"]
MARKET = ["volatility", "selloff", "risk"]

KEYWORD_WEIGHTS = {
    "gold": (GOLD, 3),
    "fed": (FED, 2),
    "inflation": (INFLATION, 2),
    "dollar": (DOLLAR, 2),
    "geo": (GEO, 1),
    "financial": (FINANCIAL, 1),
    "market": (MARKET, 1),
}


def count_matches(content, keywords):
    """
    Cuenta cuántas palabras clave aparecen en el contenido.
    """
    return sum(1 for keyword in keywords if keyword in content)


def get_matched_keywords(content):
    """
    Devuelve un set con todas las keywords detectadas en el titular.
    """
    content = content.lower()
    matched = set()
    for keywords, _weight in KEYWORD_WEIGHTS.values():
        for keyword in keywords:
            if keyword in content:
                matched.add(keyword)
    return matched


def calculate_score(content):
    """
    Calcula score base según impacto macroeconómico.
    """
    content = content.lower()

    score = 0
    for keywords, weight in KEYWORD_WEIGHTS.values():
        score += count_matches(content, keywords) * weight

    return score


def calculate_burst_bonus(content, hot_keywords, bonus_per_keyword=1, max_bonus=3):
    """
    Suma bonus si el titular contiene keywords repetidas en el ciclo.
    """
    if not hot_keywords:
        return 0

    matched = get_matched_keywords(content)
    burst_hits = len(matched.intersection(hot_keywords))
    return min(burst_hits * bonus_per_keyword, max_bonus)


def classify(score):
    """
    Clasifica el impacto según score final.
    """
    if score >= 7:
        return "🔥 ALTO IMPACTO"
    elif score >= 4:
        return "⚠️ MEDIO IMPACTO"
    return None
