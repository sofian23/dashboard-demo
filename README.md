# Automatisk dashboard: e-conomic → Google Sheets → Looker Studio

Hver nat henter et lille Python-script de bogførte fakturaer fra e-conomic, regner omsætning pr. måned og pr. kunde ud og gemmer det som CSV. Google Sheets henter filerne, og Looker Studio viser dem som et dashboard, der opdaterer sig selv.

```
e-conomic API ──(hver nat, GitHub Actions)──> data/*.csv ──> Google Sheets ──> Looker Studio
```

Demoen bruger **e-conomic's offentlige demo-regnskab**, så tallene er rigtige API-data, ikke noget du selv har fundet på. Den koster 0 kr., og du skal ikke have adgang til en kundes regnskab.

Samlet tid: ca. 1–1,5 time.

---

## 1. Kør scriptet på din egen computer (5 min.)

```bash
python3 hent_data.py
```

Der kommer to filer i `data/`: `maaneder.csv` og `kunder.csv`. Åbn dem og tjek, at der står tal i dem.

## 2. Læg projektet på GitHub (10 min.)

1. Opret et nyt **offentligt** repository på github.com, fx `dashboard-demo`. Det skal være offentligt, for at Google Sheets kan læse filerne. Det er fint, fordi demodata ikke er hemmelige.
2. Upload alle filer, også mappen `.github/workflows`. Mappen er skjult på Mac, så tryk `Cmd + Shift + .` i Finder for at se den.
3. Gå til fanen **Actions**, vælg "Opdater dashboard-data" og tryk **Run workflow**. Efter et minut skal kørslen være grøn, og `data/` er opdateret.

Fra nu af kører den automatisk hver nat.

## 3. Hent tallene ind i Google Sheets (10 min.)

1. Opret et nyt Google Sheet med to faner: `Maaneder` og `Kunder`.
2. Find filens "raw"-adresse: Åbn `data/maaneder.csv` på GitHub og tryk **Raw**. Adressen ligner
   `https://raw.githubusercontent.com/DIT-BRUGERNAVN/dashboard-demo/main/data/maaneder.csv`
3. Skriv i celle A1 på fanen `Maaneder`:
   ```
   =IMPORTDATA("https://raw.githubusercontent.com/DIT-BRUGERNAVN/dashboard-demo/main/data/maaneder.csv"; ","; "en_US")
   ```
   Gør det samme med `kunder.csv` på fanen `Kunder`.

   `"en_US"` er vigtigt. Ellers læser et dansk Google Sheet `1234.50` som et forkert tal. Hvis dit ark bruger komma i formler, så skift `;` ud med `,`.

Google Sheets henter filerne igen af sig selv, ca. hver time.

## 4. Byg dashboardet i Looker Studio (30–45 min.)

1. Gå til **lookerstudio.google.com** → **Opret** → **Rapport** → **Google Sheets** → vælg dit ark og fanen `Maaneder`.
2. Tilføj fanen `Kunder` som endnu en datakilde: **Ressource** → **Administrer tilføjede datakilder** → **Tilføj**.
3. Tjek felttyperne: `maaned` skal være **Dato**, og `omsaetning` skal være **Valuta (DKK)**.
4. Byg siden:
   - **Overskrift** med kundens navn og "Opdateres automatisk hver nat"
   - **Scorecards**: samlet omsætning, antal fakturaer og gennemsnit pr. faktura (felt: `omsaetning / fakturaer`)
   - **Søjlediagram**: omsætning pr. måned (dimension `maaned`, metrik `omsaetning`)
   - **Vandret søjlediagram**: top 10 kunder efter omsætning
   - **Datofilter** øverst, så man kan vælge periode
5. Giv den dit eget præg: farver, dit logo og "Lavet af [dit navn/firma]" i hjørnet.
6. **Del** → "Alle med linket kan se". Det er det link, du sender til kunderne.

## 5. Når du får en rigtig kunde

1. Opret en gratis udviklerkonto hos e-conomic og en app. Så får du en **App Secret Token**.
2. Kunden godkender din app med ét klik og får en **Agreement Grant Token**, som de sender til dig.
3. Gør kundens repository **privat**, og læg de to tokens ind under **Settings → Secrets and variables → Actions** med navnene `ECONOMIC_APP_SECRET_TOKEN` og `ECONOMIC_AGREEMENT_GRANT_TOKEN`.
4. Et privat repository kan Google Sheets ikke læse direkte. Til rigtige kunder skal scriptet derfor skrive direkte til Google Sheets eller BigQuery med en service-konto. Det kan vi bygge, når du lander den første kunde.

Med omkostninger og dækningsbidrag (fra e-conomic's konti/posteringer) kan dashboardet udvides til det fulde overblik over omsætning, dækningsgrad, resultat og likviditet.
