import os
import sys
import requests
from playwright.sync_api import sync_playwright

URL = "https://tixforgigs.shop/de/events/75574"
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
            extra_http_headers={"Accept-Language": "de-DE,de;q=0.9"},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
        )
        page = context.new_page()
        page.goto(URL, wait_until="networkidle", timeout=45000)
        page.wait_for_selector("text=Stammgast Special", timeout=30000)
        page.wait_for_timeout(2000)

        visible_text = page.inner_text("body")
        text_lower = visible_text.lower()
        alerts = []

        # Check 1: Offizieller Wiederverkauf / Resale sichtbar
        if "wiederverkauf" in text_lower or "resale" in text_lower:
            alerts.append("Der Bereich 'Wiederverkauf' / 'Resale' ist auf der Seite sichtbar!")

        # Check 2: Prüfen, ob einer der ersten 5 '+'-Buttons (Festivaltickets) aktiv/klickbar ist
        add_buttons = page.locator("button:has-text('add')")
        total_buttons = add_buttons.count()
        festival_buttons_to_check = min(5, total_buttons)

        available_count = 0
        for i in range(festival_buttons_to_check):
            if add_buttons.nth(i).is_enabled():
                available_count += 1

        print(
            f"Aktueller Status: {available_count}/{festival_buttons_to_check} "
            f"Festivaltickets kaufbar (gesamt {total_buttons} Plus-Buttons gefunden)."
        )

        if available_count > 0:
            alerts.append(
                f"Mindestens ein Festivalticket ist kaufbar ({available_count} aktive Plus-Buttons)!"
            )

        browser.close()

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
