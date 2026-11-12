"""
Henter bogførte fakturaer fra e-conomic og laver to CSV-filer til dashboardet:

  data/maaneder.csv  – omsætning og antal fakturaer pr. måned
  data/kunder.csv    – omsætning og antal fakturaer pr. kunde

Uden opsætning bruger scriptet e-conomic's offentlige demo-regnskab (kun læseadgang).
Til en rigtig kunde sætter du to miljøvariabler:

  ECONOMIC_APP_SECRET_TOKEN      – din apps "secret token" fra e-conomic's udviklerportal
  ECONOMIC_AGREEMENT_GRANT_TOKEN – kundens "grant token", som de giver, når de godkender din app

Kræver kun Python 3.9+ (ingen ekstra pakker).
"""

import csv
import json
import os
import sys
import time
import urllib.request
from collections import defaultdict
from pathlib import Path

BASE_URL = "https://restapi.e-conomic.com"
PAGE_SIZE = 1000
OUT_DIR = Path(__file__).parent / "data"

HEADERS = {
    "X-AppSecretToken": os.environ.get("ECONOMIC_APP_SECRET_TOKEN", "demo"),
    "X-AgreementGrantToken": os.environ.get("ECONOMIC_AGREEMENT_GRANT_TOKEN", "demo"),
    "Content-Type": "application/json",
}


def get(url: str) -> dict:
    """GET med op til 3 forsøg, hvis e-conomic svarer langsomt eller fejler midlertidigt."""
    for forsoeg in range(3):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=60) as resp:
                return json.load(resp)
        except Exception as e:  # noqa: BLE001
            if forsoeg == 2:
                raise
            print(f"Fejl ({e}), prøver igen ...", file=sys.stderr)
            time.sleep(2 * (forsoeg + 1))
    return {}


def hent_alle(endpoint: str) -> list[dict]:
    """Henter alle sider fra et endpoint (e-conomic giver højst 1.000 pr. side)."""
    rows, side = [], 0
    while True:
        data = get(f"{BASE_URL}{endpoint}?skippages={side}&pagesize={PAGE_SIZE}")
        rows.extend(data.get("collection", []))
        if not data.get("pagination", {}).get("nextPage"):
            return rows
        side += 1


def lav_eksempel_fakturaer() -> list[dict]:
    """
    Opdigtede fakturaer for en lille virksomhed: 12 måneder op til i dag, 14 kunder.
    Samme format som e-conomic's API, så resten af scriptet er det samme.
    Bruges kun til demo – start scriptet med  --eksempel
    """
    import datetime
    import random

    rnd = random.Random(42)  # fast "frø", så tallene er de samme hver gang
    kunder = [
        ("Byggefirma Nord ApS", 9), ("Boligforeningen Sølyst", 7), ("Erhverv Øst ApS", 6),
        ("Københavns Kommune", 6), ("Andelsboligforeningen Lindely", 4), ("Malerfirma Jensen", 4),
        ("Ejendomsselskabet Havnen", 3), ("Café Torvet", 2), ("Tandlæge Holm", 2),
        ("Skovgaard Arkitekter", 2), ("Privatkunde", 8), ("Grøn Have I/S", 2),
        ("Nordvest Fitness", 1), ("Bageriet på Hjørnet", 1),
    ]
    navne = [k for k, _ in kunder]
    vaegte = [v for _, v in kunder]
    saeson = [0.75, 0.8, 0.95, 1.05, 1.15, 1.2, 0.85, 1.0, 1.15, 1.2, 1.1, 0.9]  # jan..dec

    idag = datetime.date.today()
    fakturaer = []
    for i in range(12):
        aar, md = divmod(idag.year * 12 + idag.month - 1 - (11 - i), 12)
        md += 1
        vaekst = 1 + 0.015 * i
        for _ in range(int(32 * saeson[md - 1] * vaekst + rnd.randint(-4, 4))):
            fakturaer.append({
                "date": f"{aar}-{md:02d}-{rnd.randint(1, 28):02d}",
                "netAmountInBaseCurrency": round(rnd.lognormvariate(9.3, 0.6), 2),
                "recipient": {"name": rnd.choices(navne, vaegte)[0]},
            })
    return fakturaer


def main() -> None:
    if "--eksempel" in sys.argv:
        fakturaer = lav_eksempel_fakturaer()
        print(f"Lavede {len(fakturaer)} eksempel-fakturaer (opdigtede tal)")
    else:
        fakturaer = hent_alle("/invoices/booked")
        print(f"Hentede {len(fakturaer)} bogførte fakturaer")
    if not fakturaer:
        sys.exit("Ingen fakturaer fundet – tjek dine tokens.")

    pr_maaned = defaultdict(lambda: {"omsaetning": 0.0, "fakturaer": 0})
    pr_kunde = defaultdict(lambda: {"omsaetning": 0.0, "fakturaer": 0})

    for f in fakturaer:
        # netAmountInBaseCurrency = beløb uden moms, omregnet til regnskabets valuta (typisk DKK)
        beloeb = float(f.get("netAmountInBaseCurrency", f.get("netAmount", 0)) or 0)
        maaned = (f.get("date") or "")[:7]  # "2026-10-14" -> "2026-10"
        kunde = (f.get("recipient") or {}).get("name") or "Ukendt kunde"

        pr_maaned[maaned]["omsaetning"] += beloeb
        pr_maaned[maaned]["fakturaer"] += 1
        pr_kunde[kunde]["omsaetning"] += beloeb
        pr_kunde[kunde]["fakturaer"] += 1

    OUT_DIR.mkdir(exist_ok=True)

    with open(OUT_DIR / "maaneder.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["maaned", "omsaetning", "fakturaer"])
        for maaned in sorted(pr_maaned):
            v = pr_maaned[maaned]
            w.writerow([f"{maaned}-01", round(v["omsaetning"], 2), v["fakturaer"]])

    with open(OUT_DIR / "kunder.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["kunde", "omsaetning", "fakturaer"])
        for kunde, v in sorted(pr_kunde.items(), key=lambda kv: -kv[1]["omsaetning"]):
            w.writerow([kunde, round(v["omsaetning"], 2), v["fakturaer"]])

    print(f"Skrev {len(pr_maaned)} måneder og {len(pr_kunde)} kunder til {OUT_DIR}/")


if __name__ == "__main__":
    main()
