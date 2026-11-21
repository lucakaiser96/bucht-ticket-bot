import os
import sys
import requests
from bs4 import BeautifulSoup

URL = "https://www.tixforgigs.com/de-DE/Event/75574/bucht-der-traumer-2027-helenesee-frankfurt-oder"
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "de-DE,de;q=0.9",
}


def send_telegram(message: str) -> None:
    if not BOT_TOKEN or not CHAT_ID:
        print("FEHLER: TELEGRAM_BOT_TOKEN oder TELEGRAM_CHAT_ID fehlt.")
        sys.exit(1)

    api_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "disable_web_page_preview": False,
    }
    resp = requests.post(api_url, json=payload, timeout=15)
    resp.raise_for_status()
    print("Telegram-Nachricht erfolgreich gesendet.")


def check_tickets() -> None:
    resp = requests.get(URL, headers=HEADERS, timeout=20)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    full_text = soup.get_text(" ", strip=True)
    full_text_lower = full_text.lower()

    alerts = []

    # Check 1: Offizieller Wiederverkauf-Bereich ist aktiv
    if "wiederverkauf" in full_text_lower:
        alerts.append("Der Bereich 'Wiederverkauf' ist auf der Seite aufgetaucht!")

    # Check 2: Eines der 4 Festivaltickets ist nicht mehr "Ausverkauft"
    # Wir schneiden gezielt den Bereich zwischen "Stammgast Special" und "Parken" aus
    start_idx = full_text_lower.find("stammgast special")
    end_idx = full_text_lower.find("parken", start_idx) if start_idx != -1 else -1

    if start_idx != -1 and end_idx != -1:
        festival_section = full_text_lower[start_idx:end_idx]
        sold_out_count = festival_section.count("ausverkauft")
        print(f"Aktueller Status: {sold_out_count}/4 Festivalticket-Phasen 'Ausverkauft'.")
        # Hinweis: Vor 'Stammgast Special' steht das erste 'Ausverkauft', daher zählen wir hier 3 innerhalb des Blocks
        if sold_out_count < 3:
            alerts.append(
                f"Mindestens eine reguläre Festivalticket-Phase ist nicht mehr ausverkauft!"
            )
    else:
        print("Hinweis: Seitenstruktur konnte nicht exakt eingegrenzt werden.")

    if alerts:
        msg = (
            "🎟️ BUCHT DER TRÄUMER 2027 ALARM!\n\n"
            + "\n".join(f"• {a}" for a in alerts)
            + f"\n\nDirektlink:\n{URL}"
        )
        send_telegram(msg)
    else:
        print("Keine Tickets verfügbar. Alles noch ausverkauft.")


if __name__ == "__main__":
    check_tickets()
