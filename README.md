# DAW_FS26 – Data Wrangling (+ Softwarekonstruktion)

Reproduzierbare Datenpipeline für die Module **Data Wrangling (DAW)** und **Softwarekonstruktion (SKO)** an der FHNW.

Die Pipeline verknüpft Katastrophenereignisse aus EM-DAT mit täglichen Meeresspiegel-Anomalien im Mittelmeer und produziert einen analysierbaren Datensatz (`flood_linked.parquet`).

---

## Datenquellen

| Datei | Format | Inhalt |
|---|---|---|
| `public_emdat_1991_2024.xlsx` | Excel | Katastrophenereignisse (EM-DAT), 1991–2024 |
| `omi_climate_sl_medsea_area_averaged_anomalies_19990220_P20250729.nc` | NetCDF | Mittelmeer-Meeresspiegel-Anomalien, 1999–2024 |

Die Rohdaten liegen in `data/raw/` und sind via **Git LFS** versioniert.

---

## Pipeline

Orchestriert in `src/myproj/pipeline.py`, läuft vollständig im Arbeitsspeicher. Jede Stufe loggt strukturiert Anzahl Datenpunkte und ausgeführte Operationen. Das Mermaid-Diagramm in `docs/pipeline.pdf` zeigt den vollständigen Ablauf.

| Schritt | Funktion | Beschreibung |
|---|---|---|
| 1 · Import | `run_import` | Rohdaten aus `data/raw/` laden (`.xlsx` via pandas, `.nc` via xarray) |
| 2 · Pre-Filter | `run_pre_filter` | Spaltenreduktion; EMDAT auf Sea-Level-Abdeckungszeitraum einschränken |
| 3 · Cleaning | `run_cleaning` | Duplikate, unmögliche Daten, fehlende Startjahre entfernen; Sea-Level interpolieren |
| 4 · Post-Filter | `run_post_filter` | EMDAT auf Flood-Ereignisse und Mittelmeerländer einschränken |
| 5 · Transform | `run_transform` | `start_date`/`end_date` konstruieren; `season`, `event_duration_days`, `has_coordinates` ergänzen |
| 6 · Join | `run_join` | Tagesgenaue Verknüpfung mit Sea-Level; Lags und Z-Scores berechnen; redundante Spalten entfernen |
| 7 · Export | `run_export` | Ergebnis als `data/processed/flood_linked.parquet` speichern |

### Finaler Datensatz

`flood_linked` enthält pro Flood-Ereignis im Mittelmeerraum:

- `start_date`, `end_date`, `start_date_quality`, `end_date_quality`
- `season`, `event_duration_days`, `has_coordinates`
- `sea_level_at_start`, `sea_trend_at_start`, `sea_level_at_end`, `mean_sea_level_while_disaster`
- `sea_level_lag_1d` bis `sea_level_lag_5d`
- `sea_level_at_start_z`, `mean_sea_level_while_disaster_z`

---

## Entwicklungsworkflow (nbdev)

Der Produktionscode in `src/myproj/` wird **aus den Notebooks generiert**, nicht manuell geschrieben. Jedes Notebook besitzt ein `#| default_exp`-Direktiv, das das Zielmodul festlegt. Mit `#| export` markierte Zellen werden via `nbdev-export` in die entsprechende `.py`-Datei exportiert.

```
notebooks/01_Import.ipynb          →  src/myproj/io/import_data.py
notebooks/02_Filter.ipynb          →  src/myproj/transform/filter.py
notebooks/03_Cleaning.ipynb        →  src/myproj/cleaning/clean.py
notebooks/04_Transform.ipynb  →  src/myproj/transform/transform.py
notebooks/05_Join.ipynb            →  src/myproj/link/join.py
notebooks/06_Export.ipynb          →  src/myproj/io/export_data.py
```

**Regel: Nie `.py`-Dateien in `src/myproj/` direkt editieren** — Änderungen würden beim nächsten `nbdev-export` überschrieben.

Typischer Ablauf:

1. Funktion im zugehörigen Notebook entwickeln und testen
2. Zelle mit `#| export` markieren
3. `nbdev-export` ausführen → `.py`-Datei wird aktualisiert
4. Unit-Test in `tests/unit/` ergänzen

```bash
uv run nbdev-export
uv run pytest
```

---

## Schnellstart

### Auswertung / Abgabe

Voraussetzung: [uv](https://github.com/astral-sh/uv) installiert.

```bash
git clone https://github.com/damiansze/DAW_FS26.git
cd DAW_FS26
uv sync --frozen
uv run python -m myproj.pipeline
```

### Entwicklung

```bash
git clone https://github.com/damiansze/DAW_FS26.git
cd DAW_FS26
uv sync
uv run pre-commit install   # Ruff Lint + Format bei jedem git commit
```

Wichtige Befehle:

```bash
uv run nbdev-export                                    # Notebooks → src/myproj/
uv run python -m myproj.pipeline                       # Pipeline ausführen
uv run pytest                                          # Tests ausführen
uv run pytest --cov=myproj --cov-report=term           # Tests + Coverage
uv run ruff check .                                    # Linting
uv run ruff format --check .                           # Format-Prüfung
```

---

## Repository-Struktur

```text
.
├── .github/workflows/ci.yml       # CI Pipeline (Lint → Tests, getrennte Jobs)
├── .pre-commit-config.yaml        # Pre-commit Hooks (Ruff Lint + Format)
├── docs/
│   └── pipeline.mmd               # Pipeline-Diagramm (Mermaid)
│   └── pipeline.pdf               # Pipeline-Diagramm (PDF)
├── notebooks/                     # Entwicklungsumgebung (Quelle für src/)
│   ├── 01_Import.ipynb
│   ├── 02_Filter.ipynb
│   ├── 03_Cleaning.ipynb
│   ├── 04_Transform.ipynb
│   ├── 05_Join.ipynb
│   └── 06_Export.ipynb
├── src/
│   └── myproj/                    # Generierter Produktionscode (via nbdev-export)
│       ├── _utils.py              # Gemeinsame Hilfsfunktionen
│       ├── pipeline.py            # Orchestrierung der gesamten Pipeline
│       ├── io/
│       │   ├── import_data.py     # Reader (Excel, NetCDF)
│       │   └── export_data.py     # Writer (Parquet)
│       ├── transform/
│       │   ├── filter.py          # Spaltenauswahl, Temporal- und Themenfilter
│       │   └── transform.py       # Datumsaufbereitung, abgeleitete Spalten, Lags, Z-Scores
│       ├── cleaning/
│       │   └── clean.py           # Duplikate, Datumsvalidierung, Imputation
│       └── link/
│           └── join.py            # Sea-Level-Join und Anreicherung
├── tests/
│   ├── unit/
│   │   ├── test_import_data.py
│   │   ├── test_export_data.py
│   │   ├── test_filter.py
│   │   ├── test_transform.py
│   │   ├── test_clean.py
│   │   └── test_join.py
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

## CI/CD & Branching

Die GitHub Actions Pipeline (`.github/workflows/ci.yml`) läuft bei jedem **Push auf `main`** und **Pull Request gegen `main`**:

- **Job 1 – Lint:** `ruff check .` + `ruff format --check .`
- **Job 2 – Tests** *(nur bei grünem Lint):* `pytest --cov=src --cov-fail-under=50`

**Branching:**
- `main` — stabiler Code, nur via PR
- Feature Branches — je Lerneinheit oder Feature (`feature/LE1-import`)

**Regel:** Nur Code mit grüner CI darf in `main` gemerged werden.

---

## Modulanforderungen

### DAW – Data Wrangling (LE1–LE4)
- **LE1 Import:** Einlesen von mindestens zwei nicht-trivialen Datenquellen
- **LE2 Cleaning:** Bereinigung und Validierung
- **LE3 Transform:** Feature Engineering, Normalisierung, Aggregation
- **LE4 Link:** Verknüpfung/Merge der Datenquellen zu einem finalen Datensatz

### SKO – Softwarekonstruktion
- **Clean Code:** PEP 8, automatisches Linting (`ruff`)
- **Testing:** Unit- und Integrationstests (`pytest`), Coverage ≥ 50 %
- **CI/CD:** GitHub Actions prüft Lint + Tests bei jedem Push/PR

---

## Tooling

| Tool | Zweck |
|---|---|
| **uv** | Dependency Management |
| **nbdev** | Notebook-zu-Produktionscode-Export |
| **ruff** | Linting und Formatting |
| **pytest + pytest-cov** | Tests und Coverage |
| **pre-commit** | Automatisches Linting bei `git commit` |
| **GitHub Actions** | CI/CD (Lint + Tests) |
| **Git LFS** | Versionierung grosser Datendateien (.xlsx, .nc) |
