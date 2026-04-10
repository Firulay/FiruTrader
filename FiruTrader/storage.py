import json
import os


def _resolve_file_path():
    file_path = os.getenv("SENT_FILE_PATH", "").strip()
    if file_path:
        return file_path

    data_dir = os.getenv("DATA_DIR", "").strip()
    if data_dir:
        return os.path.join(data_dir, "sent.json")

    return "sent.json"


FILE = _resolve_file_path()


def load_sent():
    """
    Carga noticias ya enviadas (para evitar duplicados).
    """
    if not os.path.exists(FILE):
        return set()

    try:
        with open(FILE, "r", encoding="utf-8") as file_obj:
            return set(json.load(file_obj))
    except (json.JSONDecodeError, OSError):
        return set()


def save_sent(sent):
    """
    Guarda noticias enviadas.
    """
    parent = os.path.dirname(FILE)
    if parent:
        os.makedirs(parent, exist_ok=True)

    with open(FILE, "w", encoding="utf-8") as file_obj:
        json.dump(list(sent), file_obj)
