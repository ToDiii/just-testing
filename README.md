# Municipality Scraper

Ein modernes Web-Dashboard zum automatisierten Scrapen von Bekanntmachungen, Bebauungsplänen und Ausschreibungen deutscher Kommunen — mit KI-Analyse, RSS-Feed-Unterstützung und interaktiver Karte.

---

## Quick Start Guide

### Proxmox LXC (empfohlen für Produktion)

```bash
# Im LXC-Container-Terminal ausführen:
bash -c "$(wget -qLO - https://raw.githubusercontent.com/ToDiii/just-testing/main/install.sh)"
```

Nach der Installation ist die App unter `http://<CONTAINER_IP>:8000` erreichbar.

### Docker Compose

```bash
git clone https://github.com/ToDiii/just-testing.git
cd just-testing
docker-compose up --build -d
docker-compose exec app python3 seed_db.py   # Testdaten laden
```

→ Erreichbar unter `http://localhost:8000`

### Server-Update (nach neuen Commits auf `main`)

Für Proxmox LXC Container reicht nun ein einfacher Befehl im Terminal (als Root):

```bash
update
```

Dieser Befehl führt automatisch ein `git pull` aus, aktualisiert alle Python- und Node-Pakete, baut das Svelte-Frontend neu und startet den Dienst (Service) neu.

*(Alternativ, für manuelle Setups: `/opt/just-testing/update.sh` ausführen)*

**Hinweis für bestehende (alte) Installationen:**
Falls deine Installation älter ist und den Befehl noch nicht kennt, rüste ihn mit diesem Einzeiler einmalig nach:
```bash
cd /opt/just-testing && git pull origin main && chmod +x update.sh && ln -sf /opt/just-testing/update.sh /usr/local/bin/update && update
```

---

## Features

| Feature | Beschreibung |
|---|---|
| **Web-Scraping** | Automatisiertes Crawlen von Gemeinde-Websites (HTML + PDF) |
| **RSS/Atom-Feeds** | Direkte Einbindung von Feed-URLs als Quelltyp |
| **Crawl4AI-Engine** | Headless-Chromium-Rendering für JS-lastige Seiten (lokal oder externer Server) |
| **KI-Analyse** | Zusammenfassung von Ergebnissen via OpenRouter / OpenAI / Anthropic |
| **Ergebnisse-Ansichten** | Tabelle, Kleine Kacheln, Große Kacheln (Präferenz in localStorage) |
| **Interaktive Karte** | Leaflet-Karte mit Umkreissuche nach PLZ/Adresse |
| **Benachrichtigungen** | Webhook- und E-Mail-Benachrichtigungen bei neuen Treffern |
| **Mobile-optimiert** | Responsive UI mit Hamburger-Menü |
| **Keyword-System** | Kategorisierte Keywords für präzises Matching |

---

## Architektur

```
just-testing/
├── webapp/              # FastAPI Backend
│   ├── main.py          # App-Einstiegspunkt, DB-Migrationen
│   ├── routes.py        # API-Routen (Scraping, Targets, Results, Config)
│   ├── ai_routes.py     # KI-Analyse API (/api/ai/*)
│   ├── ai_service.py    # Multi-Provider Chat Completion
│   ├── models.py        # SQLAlchemy-Modelle
│   ├── schemas.py       # Pydantic-Schemas
│   └── notifications.py # Webhook/E-Mail-Versand
├── scraper_lib/         # Scraping-Bibliothek
│   ├── fetcher.py       # HTTP-Fetching (requests)
│   ├── crawl4ai_fetcher.py  # Crawl4AI lokal & remote
│   ├── feed_fetcher.py  # RSS/Atom-Feed-Parser
│   ├── parser.py        # HTML-Parsing (BeautifulSoup)
│   ├── extractor.py     # Keyword-Matching
│   └── ocr.py           # PDF-OCR (Tesseract)
├── scraper.py           # Scraper-Klasse (requests-Engine)
├── scraper_crawl4ai.py  # Crawl4AIScraper-Klasse
├── src/                 # Svelte + Tailwind Frontend
│   ├── App.svelte        # Haupt-App, Navigation
│   └── lib/components/
│       ├── Dashboard.svelte       # Karte + Umkreissuche
│       ├── ResultsViewer.svelte   # Ergebnisse + KI-Analyse-Button
│       ├── TargetManager.svelte   # Ziele + Keywords verwalten
│       └── AdminDashboard.svelte  # Einstellungen (Engine, KI, Limits)
└── install.sh           # Proxmox LXC Installer
```

---

## Admin-Einstellungen

### Scraping-Limits
| Einstellung | Standard | Beschreibung |
|---|---|---|
| Max. HTML Links | 15 | Unterseiten pro Kommune |
| Max. PDF Links | 10 | PDF-Dokumente pro Website |
| Abfrage-Verzögerung | 0.5s | Pause zwischen Requests |
| Max. Ziele pro Durchlauf | 500 | 0 = unbegrenzt |

### Scraping-Engine
- **requests + BeautifulSoup** (Standard) — schnell, kein Browser, kein zusätzliches Setup
- **Crawl4AI** — Headless Chromium, rendert JavaScript
  - Lokal: `crawl4ai` muss installiert sein
  - Extern: Docker-Container auf anderem Host → URL eintragen (z.B. `http://192.168.1.100:11235`)
  - Fallback auf `requests` bei Fehler konfigurierbar

### KI-Analyse
Unterstützte Anbieter:
- **OpenRouter** (empfohlen) — Zugang zu vielen Modellen mit einem API-Key
- **OpenAI** — `gpt-4o`, `gpt-4o-mini` etc.
- **Anthropic** — `claude-3-5-haiku`, `claude-3-5-sonnet` etc.
- **Custom** — Beliebige OpenAI-kompatible API (eigene URL angeben)

Standard-Modell: `openai/gpt-4o-mini` (via OpenRouter)

### RSS/Atom-Feeds
Beim Hinzufügen eines Ziels den Quelltyp **RSS/Atom Feed** wählen (oder Feed-URLs werden automatisch erkannt). Feed-Ziele werden direkt geparst, ohne Scraping-Engine.

---

## Entwicklung

### Lokales Setup

```bash
# Python-Backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn webapp.main:app --reload

# Frontend (separates Terminal)
cp .env.example .env   # VITE_API_KEY=dev setzen
npm install
npm run dev
```

- Backend API: `http://localhost:8000`
- Frontend Dev Server: `http://localhost:5173`
- API Docs (Swagger): `http://localhost:8000/api/docs`

### Tests

```bash
python3 -m pytest
```

### Datenbank befüllen

```bash
# Kleine Testmenge (6 bayerische Kommunen)
python3 seed_db.py

# Vollimport (>10.000 Gemeinden, dauert lange)
python3 import_data.py

# Begrenzt testen
python3 import_data.py --limit 100
```

---

## Proxmox LXC Installation (Detail)

1. **LXC-Container erstellen**: Debian 12 oder Ubuntu 24.04, empfohlen: 2 vCPUs, 4 GB RAM, 32 GB Storage
2. **Installer ausführen**:
   ```bash
   bash -c "$(wget -qLO - https://raw.githubusercontent.com/ToDiii/just-testing/main/install.sh)"
   ```
3. Nach der Installation: `http://<CONTAINER_IP>:8000`

Der Installer richtet ein Python-venv, den Svelte-Build und einen systemd-Service (`just-testing.service`) ein.

---

## Docker Compose (Development)

```bash
# Mit Live-Reload
docker-compose -f docker-compose.dev.yml up --build

# Backend:   http://localhost:8000
# Frontend:  http://localhost:5173
```
