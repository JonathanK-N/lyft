from urllib.parse import quote_plus

def wa_link(phone: str, text: str = "Bonjour !"):
    return f"https://wa.me/{phone}?text={quote_plus(text)}"
