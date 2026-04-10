from deep_translator import GoogleTranslator

def translate(text):
    """
    Traduce texto al español
    """
    try:
        return GoogleTranslator(source='auto', target='es').translate(text)
    except:
        return text  # fallback si falla