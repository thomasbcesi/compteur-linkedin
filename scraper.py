import html
import json
import os
import re
import subprocess
from datetime import datetime, timezone

COMPANY = os.environ.get("LINKEDIN_COMPANY", "").strip()
if not COMPANY:
    raise SystemExit("::error::Secret LINKEDIN_COMPANY manquant ou vide")

URL = f"https://www.linkedin.com/company/{COMPANY}"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/130.0 Safari/537.36")

# Nombre (espaces normales, insécables U+00A0 / U+202F, points, virgules)
# suivi de abonnés / followers
PATTERN = re.compile(
    r"(\d[\d\s.,\u00a0\u202f]*\d|\d)\s*(?:abonnés|abonné|followers|follower)",
    re.IGNORECASE,
)
META_DESC = re.compile(
    r'<meta\s+name="description"\s+content="([^"]*)"', re.IGNORECASE
)


def fetch():
    r = subprocess.run(
        ["curl", "-sL", "--max-time", "30",
         "-A", UA,
         "-H", "Accept-Language: fr-FR,fr;q=0.9",
         "-w", "\n%{http_code}",
         URL],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    body, _, code = r.stdout.rpartition("\n")
    return code.strip(), body


def parse_number(text):
    m = PATTERN.search(text)
    if not m:
        return None
    digits = re.sub(r"\D", "", m.group(1))
    return int(digits) if digits else None


def extract(page):
    # 1) d'abord dans la balise meta description
    m = META_DESC.search(page)
    if m:
        n = parse_number(html.unescape(m.group(1)))
        if n is not None:
            return n
    # 2) sinon dans toute la page
    return parse_number(html.unescape(page))


def main():
    code, page = fetch()
    if code != "200":
        print(f"::warning::LinkedIn a répondu avec le code HTTP {code}, compteur inchangé")
        return

    followers = extract(page)
    if followers is None:
        print("::warning::Nombre d'abonnés introuvable dans la page, compteur inchangé")
        return

    data = {
        "followers": followers,
        "updated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(data, f)
    print(f"Abonnés : {followers}")


if __name__ == "__main__":
    main()
