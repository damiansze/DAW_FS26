# DAW_FS26 – Data Wrangling (+ Softwarekonstruktion)

Dieses Repository ist die gemeinsame Basis für die Module **Data Wrangling (DAW)** und **Softwarekonstruktion (SKO)**.  
Ziel ist eine reproduzierbare Datenpipeline (Import → Bereinigen → Transformieren → Verknüpfen) mit Clean Code, automatisierten Tests und CI/CD.

---

## Projektübersicht

### DAW – Data Wrangling (LE1–LE4)
- **LE1 Import:** Einlesen von mindestens zwei nicht-trivialen Datenquellen
- **LE2 Cleaning:** Bereinigung und Validierung
- **LE3 Transform:** Feature Engineering, Normalisierung, Aggregation
- **LE4 Link:** Verknüpfung/Merge der Datenquellen zu einem finalen Datensatz

### SKO – Softwarekonstruktion
- **Clean Code:** Einhaltung von PEP 8 und automatisches Linting (`ruff`)
- **Automated Testing:** Unit Tests für Daten-Konsistenz und Transformationslogik (`pytest`)
- **CI/CD:** GitHub Actions Pipeline prüft bei jedem Push/PR: Dependencies, Lint, Tests, Coverage
- **Code Coverage:** Mindestabdeckung wird gemessen (`pytest-cov`)

### Datenquellen
1. **EM-DAT Disaster Data**  
   Excel-Datei mit Ereignisdaten zu Katastrophen (`public_emdat_1991_2024.xlsx`).  
   Die Datei enthält Informationen zu Katastrophentypen, betroffenen Ländern, Zeitpunkten und weiteren ereignisbezogenen Merkmalen.

2. **Climate Anomaly Data**  
   NetCDF-Datei mit klimabezogenen Anomaliedaten (`omi_climate_sl_medsea_area_averaged_anomalies_19990220_P20250729.nc`).  
   Die Datei ist als xarray-Dataset strukturiert und enthält zeitbezogene Messwerte bzw. Anomalien, die später mit den Ereignisdaten in Beziehung gesetzt werden können.

### Importlogik
Der Datenimport wird über allgemeine Funktionen in `src/myproj/io/import_data.py` umgesetzt.  
Die Rohdaten werden aus dem Ordner `data/raw/` geladen. Je nach Dateiendung werden unterschiedliche Reader verwendet:

- `.xlsx`, `.xls` → `pandas.read_excel()`
- `.nc` → `xarray.open_dataset(..., engine="h5netcdf")`

Dadurch ist der Import flexibel und kann auch für weitere Rohdatenquellen wiederverwendet werden.


### Aktueller Projektstand
Aktuell liegt der Fokus auf **LE1 Import** und der technischen Projektstruktur.  
Die Rohdaten werden aus `data/raw/` geladen und im Notebook explorativ untersucht.  
Der Importcode ist im Paket `myproj.io` gekapselt, sodass dieselbe Logik später auch in der Pipeline wiederverwendet werden kann.

### Linking-Strategie & finaler Datensatz
_(TODO: Beschreibung der Verknüpfungslogik und vom finalen Outputs ergänzen)_

---

## Quickstart

### 1. Repository klonen
```bash
git clone https://github.com/damiansze/DAW_FS26.git
cd DAW_FS26
```

### 2. Dependencies installieren (uv)
Stelle sicher, dass [uv](https://github.com/astral-sh/uv) installiert ist:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Dann:
```bash
uv sync
```
Das installiert die Projekt- und Dev-Abhängigkeiten aus `pyproject.toml` und `uv.lock` in ein venv.

### 3. Pipeline ausführen
```bash
uv run python -m myproj.pipeline
```
**Output:** Erzeugt Dateien in `data/processed/` (z. B. `example.parquet`).

### 4. Tests ausführen
```bash
uv run pytest
```

### 5. Pre-commit Hooks einrichten
```bash
uv run pre-commit install
```
Damit wird bei jedem `git commit` automatisch **Ruff Lint + Format** geprüft.

### 6. Linting manuell prüfen
```bash
uv run ruff check .
uv run ruff format --check .
```

### 7. Code Coverage messen
```bash
uv run pytest --cov=myproj --cov-report=term --cov-report=html
```
**Output:** Zusammenfassung im Terminal + HTML-Report in `htmlcov/`.

---

## Repository-Struktur

```text
.
├─ .github/workflows/ci.yml      # CI Pipeline (Lint → Tests, getrennte Jobs)
├─ .pre-commit-config.yaml       # Pre-commit Hooks (Ruff Lint + Format)
├─ notebooks/                    # Jupyter Notebooks (Exploration/Dokumentation)
│  ├─ 01_import.ipynb            # (geplant) Datenimport explorieren
│  ├─ 02_clean.ipynb             # (geplant) Bereinigung dokumentieren
│  ├─ 03_transform.ipynb         # (geplant) Transformationen testen
│  └─ 04_link.ipynb              # (geplant) Verknüpfung visualisieren
├─ src/
│  └─ myproj/                    # Projektpaket (Produktionscode)
│     ├─ __init__.py
│     ├─ pipeline.py             # Orchestrierung (run_import, run_all)
│     ├─ config.py               # Pfad-Konstanten
│     ├─ io/                     # Reader/Writer (Datenimport/-export)
│     ├─ cleaning/               # Bereinigung/Validierung
│     ├─ transform/              # Feature Engineering/Transformationen
│     └─ link/                   # Verknüpfen/Joins/Matching
├─ tests/                        # pytest Unit Tests
│  └─ test_pipeline.py
├─ data/
│  ├─ raw/                       # Rohdaten (unverändert, NICHT bearbeiten)
│  └─ processed/                 # Erzeugte Ergebnisse (reproduzierbar)
├─ pyproject.toml                # Projekt-Konfiguration (Dependencies, Tools)
├─ uv.lock                       # Locked Dependencies (für Reproduzierbarkeit)
└─ README.md                     # Diese Datei
```

---

## Reproduzierbarkeit

### Datenmanagement-Policy
- **`data/raw/`:** Original-Rohdaten, **niemals bearbeiten**. Bei Bedarf lokal hinzufügen.
- **`data/processed/`:** Von der Pipeline erzeugte Outputs. Können jederzeit neu generiert werden.
- **Git LFS / DVC:** Für grosse Datasets optional in Zukunft (Je nachdem welche Daten wir nutzen).

### Exakte Schritte zur Reproduktion
1. `git clone <REPO_URL> && cd DAW_FS26`
2. `uv sync --frozen` (installiert exakte Versionen aus `uv.lock`)
3. Rohdaten in `data/raw/` ablegen (falls lokal vorhanden)
4. `uv run python -m myproj.pipeline` (Pipeline ausführen)
5. Outputs in `data/processed/` prüfen

---

## Notebooks vs. Produktionscode

- **Notebooks (`notebooks/`):** Dokumentation, Exploration, ...
- **Produktionscode (`src/myproj/`):** Wiederverwendbare, getestete Funktionen. Ist testbar, versionierbar und wird von der Pipeline verwendet.

**Workflow:** Experimente zuerst im Notebook, dann stabile Logik nach `src/` extrahieren und testen.

---

## CI/CD (GitHub Actions)

### Was wird geprüft?
Die Pipeline (`.github/workflows/ci.yml`) führt bei jedem **Push auf `main`** und **Pull Request gegen `main`** folgende Jobs aus:

**Job 1 – Lint (Ruff)**
1. Checkout Code
2. Install uv & Sync Dependencies (`uv sync --frozen`)
3. `ruff check .` → Code-Stil und Best Practices
4. `ruff format --check .` → Formatting-Konsistenz

**Job 2 – Tests (pytest)** *(läuft nur, wenn Lint erfolgreich)*
1. Checkout Code
2. Install uv & Sync Dependencies (`uv sync --frozen`)
3. `pytest --cov=src --cov-fail-under=50` → Tests + Coverage

### Status prüfen
- **GitHub:** `Actions`-Tab im Repository → grüner Haken = CI erfolgreich
- **Pull Requests:** CI-Status wird automatisch angezeigt

**Regel:** Nur Code mit grüner CI darf in `main` gemerged werden!

---

## Team-Workflow

### Branching-Strategie
- **`main`-Branch:** Stabiler, produktiver Code (nur via PR)
- **Feature Branches:** Für jede zu implementierende Lerneinheit.

### Workflow
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
