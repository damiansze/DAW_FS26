# DAW_FS26 – Data Wrangling (+ Softwarekonstruktion)

Dieses Repository ist die gemeinsame Basis für die Module **Data Wrangling (DAW)** und **Softwarekonstruktion (SKO)**.  
Ziel ist eine reproduzierbare Datenpipeline mit Clean Code, automatisierten Tests und CI/CD.

---

## Projektübersicht

### DAW – Data Wrangling (LE1–LE4)
- **LE1 Import:** Einlesen von mindestens zwei nicht-trivialen Datenquellen
- **LE2 Cleaning:** Bereinigung und Validierung
- **LE3 Transform:** Feature Engineering, Normalisierung, Aggregation
- **LE4 Link:** Verknüpfung/Merge der Datenquellen zu einem finalen Datensatz

### SKO – Softwarekonstruktion
- **Clean Code:** PEP 8, automatisches Linting (`ruff`)
- **Testing:** Unit- und Integrationstests (`pytest`), Coverage ≥ 50 %
- **CI/CD:** GitHub Actions prüft Lint + Tests bei jedem Push/PR
- **Code Coverage:** Mindestabdeckung wird gemessen (`pytest-cov`)

### Datenquellen
| Datei | Format | Inhalt |
|---|---|---|
| `public_emdat_1991_2024.xlsx` | Excel | Katastrophenereignisse (EM-DAT), 1991–2024 |
| `omi_climate_sl_medsea_area_averaged_anomalies_19990220_P20250729.nc` | NetCDF | Mittelmeer-Meeresspiegel-Anomalien, 1999–2024 |

### Pipeline
Die Datenpipeline ist in `src/myproj/pipeline.py` orchestriert und läuft vollständig im Arbeitsspeicher ohne Zwischenspeicherung:

- **Import (`run_import`):** Rohdaten werden aus `data/raw/` geladen. `.xlsx` via `pandas`, `.nc` via `xarray (h5netcdf)`.
- **Transform (`run_transform`):** Spaltenreduktion auf relevante Felder; EMDAT-Einträge eindeutig vor dem ersten Meeresspiegel-Messwert (1999-02-20) werden entfernt.
- **Cleaning (`run_cleaning`):** Duplikate, logisch unmögliche Datumsangaben und Einträge ohne Startjahr werden entfernt; fehlende Sea-Level-Messwerte werden per linearer Interpolation imputiert.

Jede Stufe loggt strukturiert, welche Operationen ausgeführt wurden und wie viele Datenpunkte betroffen waren. In `docs` ist die Pipeline aufgezeichnet zu sehen.

### Aktueller Projektstand
Import, Transform und Cleaning sind implementiert und getestet. Die nächsten Schritte sind weitere Transformationen und Verknüpfung beider Datensätze.

### Linking-Strategie & finaler Datensatz
_(TODO: Beschreibung der Verknüpfungslogik und vom finalen Outputs ergänzen)_

---

## Für Nutzer (Auswertung / Abgabe)

Voraussetzung: [uv](https://github.com/astral-sh/uv) installiert. Die Rohdaten sind via Git LFS im Repository enthalten und werden beim Klonen automatisch heruntergeladen.

```bash
git clone https://github.com/damiansze/DAW_FS26.git
cd DAW_FS26
uv sync --frozen
uv run python -m myproj.pipeline
```

---

## Für Mitentwickler

### 1. Setup

Repository klonen:
```bash
git clone https://github.com/damiansze/DAW_FS26.git
cd DAW_FS26
```

Dependencies installieren (setzt [uv](https://github.com/astral-sh/uv) voraus):
```bash
uv sync
```

Pre-commit Hooks einrichten (Ruff Lint + Format bei jedem `git commit`):
```bash
uv run pre-commit install
```

### 2. Pipeline ausführen
```bash
uv run python -m myproj.pipeline
```

### 3. Tests ausführen
```bash
uv run pytest
```

### 4. Linting manuell prüfen
```bash
uv run ruff check .
uv run ruff format --check .
```

### 5. Code Coverage messen
```bash
uv run pytest --cov=myproj --cov-report=term --cov-report=html
```
HTML-Report in `htmlcov/`.

### 6. CI/CD (GitHub Actions)

Die Pipeline (`.github/workflows/ci.yml`) führt bei jedem **Push auf `main`** und **Pull Request gegen `main`** folgende Jobs aus:

**Job 1 – Lint (Ruff)**
1. Checkout Code
2. Install uv & Sync Dependencies (`uv sync --frozen`)
3. `ruff check .` → Code-Stil und Best Practices
4. `ruff format --check .` → Formatting-Konsistenz

**Job 2 – Tests (pytest)** *(läuft nur, wenn Lint erfolgreich)*
1. Checkout Code (inkl. Git LFS)
2. Install uv & Sync Dependencies (`uv sync --frozen`)
3. `pytest --cov=src --cov-fail-under=50` → Tests + Coverage

Status prüfen: `Actions`-Tab im Repository. **Regel:** Nur Code mit grüner CI darf in `main` gemerged werden.

### 7. Branching-Strategie
- **`main`-Branch:** Stabiler, produktiver Code (nur via PR)
- **Feature Branches:** Für jede zu implementierende Lerneinheit.

Workflow:
1. **Feature Branch erstellen:**
   ```bash
   git checkout -b feature/LE1-import
   ```
2. **Arbeit committen:**
   ```bash
   git add .
   git commit -m "Add CSV reader for data source A"
   git push origin feature/LE1-import
   ```
3. **Pull Request (PR) öffnen:**
   - In GitHub: `New Pull Request`
   - CI muss grün sein
   - Mindestens 1 Review von Teammitglied erforderlich
4. **Merge nach `main`**

---

## Repository-Struktur

```text
.
├── .github/workflows/ci.yml       # CI Pipeline (Lint → Tests, getrennte Jobs)
├── .pre-commit-config.yaml        # Pre-commit Hooks (Ruff Lint + Format)
├── notebooks/                     # Jupyter Notebooks (Exploration/Dokumentation)
│   ├── 01_Import.ipynb
│   ├── 02_Transform.ipynb
│   └── 03_Cleaning.ipynb
├── src/
│   └── myproj/                    # Projektpaket (Produktionscode)
│       ├── _utils.py              # Gemeinsame Hilfsfunktionen
│       ├── pipeline.py            # Orchestrierung (run_import, run_transform, run_cleaning)
│       ├── io/
│       │   └── import_data.py     # Reader (Excel, NetCDF)
│       ├── transform/
│       │   └── trim_data.py       # Spaltenauswahl, Temporalfilter
│       ├── cleaning/
│       │   └── clean.py           # Duplikate, Datumsvalidierung, Imputation
│       └── link/                  # (ausstehend)
├── tests/
│   ├── unit/
│   │   ├── test_import_data.py
│   │   ├── test_trim_data.py
│   │   └── test_clean.py
│   └── integration/
│       └── test_pipeline.py
├── data/
│   ├── raw/                       # Rohdaten (unverändert, via Git LFS)
│   └── processed/                 # Erzeugte Ergebnisse (reproduzierbar)
├── pyproject.toml                 # Projekt-Konfiguration (Dependencies, Tools)
├── uv.lock                        # Locked Dependencies (für Reproduzierbarkeit)
└── README.md
```

---

## Notebooks vs. Produktionscode

- **Notebooks (`notebooks/`):** Dokumentation, Exploration, ...
- **Produktionscode (`src/myproj/`):** Wiederverwendbare, getestete Funktionen. Ist testbar, versionierbar und wird von der Pipeline verwendet.

**Workflow:** Experimente zuerst im Notebook, dann stabile Logik nach `src/` extrahieren und testen.

---

## Tooling

| Tool | Zweck |
|------|-------|
| **Python** | Programmiersprache |
| **uv** | Dependency Management (schneller als pip/poetry) |
| **pyproject.toml + uv.lock** | Projekt-Konfiguration + Locked Dependencies |
| **Jupyter Notebooks** | Exploration, Dokumentation |
| **ruff** | Linting und Formatting |
| **pytest** | Unit Testing Framework |
| **pytest-cov** | Code Coverage Messung |
| **pre-commit** | Git Hooks für automatisches Linting bei jedem Commit |
| **GitHub Actions** | CI/CD Pipeline (Lint + Tests) |
| **Git/GitHub** | Version Control und Kollaboration |
| **Git LFS** | Versionierung grosser Datendateien (.xlsx, .nc) |
