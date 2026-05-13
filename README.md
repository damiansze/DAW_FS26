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
- **Explorativer Transform & Join (`04_Transform_Join.ipynb`):** Flood-Ereignisse werden auf den Mittelmeerraum gefiltert, mit Datums- und Saisonspalten erweitert und mit täglichen Sea-Level-Werten verknüpft. Dieser Schritt ist aktuell noch Notebook-Code und noch nicht Teil der produktiven Pipeline.


Jede Stufe loggt strukturiert, welche Operationen ausgeführt wurden und wie viele Datenpunkte betroffen waren. In `docs` ist die Pipeline aufgezeichnet zu sehen.

### Aktueller Projektstand
Import, erste Transformation und Cleaning sind als Produktionscode in `src/myproj/` implementiert und getestet.

Zusätzlich wurde mit `notebooks/04_Transform_Join.ipynb` ein explorativer Schritt für weitere Transformationen und den Join der EMDAT- und Sea-Level-Daten erstellt. Das Notebook filtert die bereinigten EMDAT-Daten auf Flood-Ereignisse im Mittelmeerraum, konstruiert Ereignisdatumswerte, ergänzt abgeleitete Spalten und verknüpft die Ereignisse mit täglichen Sea-Level-Werten.

Die Join-Logik ist aktuell noch im Notebook umgesetzt und noch nicht vollständig als Produktionscode in `src/myproj/link/` ausgelagert.


### Linking-Strategie & finaler Datensatz

Die Linking-Strategie wird in `notebooks/04_Transform_Join.ipynb` entwickelt. Ausgangspunkt sind die bereits importierten, transformierten und bereinigten Daten aus der Pipeline.

Der Ablauf im Notebook:

1. **Flood-Filter:** Aus den bereinigten EMDAT-Daten werden nur Ereignisse behalten, bei denen `Disaster Type` oder `Disaster Subtype` auf Flood hinweist.
2. **Geographischer Filter:** Die Flood-Ereignisse werden auf Mittelmeer-Länder eingeschränkt, da der Sea-Level-Datensatz den Mittelmeerraum beschreibt.
3. **Datumsaufbereitung:** Aus `Start Year`, `Start Month`, `Start Day` sowie den End-Datumsspalten werden `start_date` und `end_date` erzeugt. Fehlende Monate oder Tage werden mit `1` ersetzt und über `start_date_quality` bzw. `end_date_quality` dokumentiert.
4. **Sea-Level-Coverage:** Es werden nur Ereignisse behalten, deren `start_date` innerhalb der Sea-Level-Zeitreihe liegt.
5. **Abgeleitete Spalten:** Ergänzt werden `season`, `event_duration_days` und `has_coordinates`.
6. **Join:** Die Flood-Ereignisse werden per Datum mit der Sea-Level-Zeitreihe verbunden.
7. **Skalierung:** Sea-Level-Werte werden zusätzlich als Z-Scores relativ zur gesamten Sea-Level-Zeitreihe berechnet.

Der finale explorative Datensatz heisst `flood_linked`. Er enthält pro Flood-Ereignis unter anderem:

- `start_date`, `end_date`
- `start_date_quality`, `end_date_quality`
- `season`
- `event_duration_days`
- `has_coordinates`
- `sea_level_at_start`
- `sea_trend_at_start`
- `sea_level_at_end`
- `mean_sea_level_while_disaster`
- `sea_level_lag_1d` bis `sea_level_lag_5d`
- `sea_level_at_start_z`
- `mean_sea_level_while_disaster_z`

Im aktuellen Notebook-Ergebnis enthält `flood_linked` **292 Flood-Ereignisse** und **31 Spalten**. Für `sea_level_at_start` fehlen keine Werte. Die Sea-Level-Zeitreihe deckt den Zeitraum **1999-02-20 bis 2024-11-19** ab.

Die Join-Logik ist aktuell noch explorativ. Als nächster Schritt sollten die stabilen Funktionen nach `src/myproj/link/` oder `src/myproj/transform/` überführt und mit Unit-Tests abgesichert werden.

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
PYTHONPATH=src uv run python -m myproj.pipeline
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
│   ├── 03_Cleaning.ipynb
│   └── 04_Transform_Join.ipynb    # Weitere Transformationen und Join
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

Beispiel: Die Join-Logik wird aktuell in `notebooks/04_Transform_Join.ipynb` entwickelt. Dort entsteht der explorative Datensatz `flood_linked`. Sobald die Logik stabil ist, sollen die Funktionen für Flood-Filter, Mittelmeer-Filter, Datumsaufbereitung, Sea-Level-Join und Skalierung in `src/myproj/link/` oder `src/myproj/transform/` übernommen und getestet werden.

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
