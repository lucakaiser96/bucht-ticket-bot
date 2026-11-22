import os
import sys
import requests
from playwright.sync_api import sync_playwright

URL = "https://www.tixforgigs.com/de-DE/Event/75574/bucht-der-traumer-2027-helenesee-frankfurt-oder"
BOT_TOKEN = (os.environ.get("TELEGRAM_BOT_TOKEN") or "").strip()
CHAT_ID = (os.environ.get("TELEGRAM_CHAT_ID") or "").strip()


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
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            locale="de-DE",
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
        )
        page = context.new_page()
        page.goto(URL, wait_until="networkidle", timeout=45000)
        page.wait_for_timeout(3000)

        # Liest nur den tatsächlich sichtbaren Text (ignoriert Skripte/Code)
        visible_text = page.inner_text("body")
        browser.close()

    text_lower = visible_text.lower()
    alerts = []

    # Check 1: Offizieller Wiederverkauf-Bereich ist sichtbar
    if "wiederverkauf" in text_lower:
        alerts.append("Der Bereich 'Wiederverkauf' ist auf der Seite sichtbar!")

    # Check 2: Eines der 4 Festivaltickets ist nicht mehr 'Ausverkauft'
    start_idx = text_lower.find("stammgast special")
    end_idx = text_lower.find("parken", start_idx) if start_idx != -1 else -1

    if start_idx != -1 and end_idx != -1:
        # 50 Zeichen vor 'stammgast special' starten, damit das erste 'Ausverkauft' mitgezählt wird
        festival_section = text_lower[max(0, start_idx - 50) : end_idx]
        sold_out_count = festival_section.count("ausverkauft")
        print(f"Aktueller Status: {sold_out_count}/4 Festivalticket-Phasen 'Ausverkauft'.")
        if sold_out_count < 4:
            alerts.append(
                "Mindestens eine reguläre Festivalticket-Phase ist nicht mehr ausverkauft!"
            )
    else:
        print("Hinweis: Seitenstruktur konnte auch mit Browser nicht eingegrenzt werden.")

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
