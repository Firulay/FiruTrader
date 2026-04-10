def is_relevant(content, score, min_gold_score=5, min_macro_score=7):
    """
    Decide si la noticia es relevante para oro/macro en modo estricto.
    """
    content = content.lower()

    has_gold_signal = any(keyword in content for keyword in ("gold", "xau", "bullion"))

    # Si habla de oro, exigimos un mínimo para evitar ruido superficial.
    if has_gold_signal and score >= min_gold_score:
        return True

    # Si no habla de oro, solo pasa cuando el impacto macro es alto.
    if score >= min_macro_score:
        return True

    return False