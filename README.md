# YottaFlex AI: Logistics Synthetic Telematics & ETA Prediction Engine

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Reproducibility: 100% Verified](https://img.shields.io/badge/Reproducibility-100%25%20Bitwise%20SHA--256-brightgreen.svg)](docs/REPRODUCIBILITY.md)
[![Validation: All Suites Passed](https://img.shields.io/badge/Validation-12%20Suites%20Passed-success.svg)](docs/VALIDATION_REPORT.md)

---

## 1. Project Summary

The **YottaFlex AI Logistics Synthetic Data Engine** is an audit-grade, causally simulated telematics and machine learning benchmark dataset. Built for freight and parcel logistics networks, it models the physical journey of shipments across multi-modal carriers, route hops, regional weather hazards, facility queue bottlenecks, and operating shift calendars.

Crucially, the dataset accurately reflects **telemetry ingestion lag** — the delay between when a physical scan occurs (`event_time`) and when it becomes visible in the central database (`ingestion_time`). This architecture enables realistic, leakage-safe ETA snapshot modeling and exposes the classic **"leakage trap"** common in naive telematics models.

---

## 2. Benchmark Results Snapshot

| Evaluation Category | Metric / Check | Score / Result | Verification Source |
|---|---|---|---|
| **Reproducibility** | Dual-Run SHA-256 Bitwise Match | **100% Identical** (23 files) | [`docs/REPRODUCIBILITY.md`](docs/REPRODUCIBILITY.md) |
| **Relational Integrity** | Foreign Key Violations | **0 orphans** (16 FK specs) | [`docs/VALIDATION_REPORT.md`](docs/VALIDATION_REPORT.md) |
| **Primary Key Integrity** | Uniqueness Across Tables | **100% Unique** (11,991 PKs) | [`docs/VALIDATION_REPORT.md`](docs/VALIDATION_REPORT.md) |
| **Temporal Consistency** | Unlabelled Chronological Inversions | **0 violations** | [`docs/VALIDATION_REPORT.md`](docs/VALIDATION_REPORT.md) |
| **Arithmetic Reconciliation** | Delay Component Sum vs Total Delay | **100% Reconciled** ($<10^{-6}\text{h}$) | [`tests/test_labels.py`](tests/test_labels.py) |
| **Anomaly Accounting** | Precision & Recall vs Ground Truth | **100% Precision / 100% Recall** | [`ground_truth/`](ground_truth/) |
| **Leakage-Safe ML ETA** | Gradient Boosted Regressor MAE | **11.07 hours** (P90: 21.94h) | [`docs/EVALUATION.md`](docs/EVALUATION.md) |
| **Leakage Trap Demo** | Leaky Model MAE (`event_time` peek) | **7.67 hours** (*Unrealistically low*) | [`docs/EVALUATION.md`](docs/EVALUATION.md) |

---

## 3. Quickstart & How to Run

### Installation
```bash
# Clone the repository
git clone https://github.com/your-username/yottaflex-eta-delay-data.git
cd yottaflex-eta-delay-data

# Install core and dashboard dependencies (Cross-platform)
python run.py install
# Alternatively on Linux/macOS: make install
```

### 1-Command Dataset Generation
```bash
# Generate Starter Dataset (500 shipments, 3,000 events, committed to repo)
python run.py starter

# Generate Full Scale Dataset (50,000 shipments, 300,000 events, 100 facilities, 1,000 disruptions)
python run.py full
```

### Validation & Quality Audit
```bash
# Run the 12-suite validation engine (generates docs/VALIDATION_REPORT.md)
python run.py validate
```

### Reproducibility Verification
```bash
# Run dual independent generations and verify bitwise SHA-256 match
python run.py repro
```

### Run Pytest Test Suite
```bash
# Execute all 24 unit and integration tests
python run.py test
```

### Launch Interactive Analytics Dashboard
```bash
# Launch Streamlit interactive operations and ML evaluation UI
python run.py dashboard
```

---

## 4. Repository Map

```
yottaflex-eta-delay-data/
├── README.md                           # Master architectural overview & quickstart
├── Makefile                            # Standard Unix target build rules
├── run.py                              # Cross-platform runner (Windows/macOS/Linux)
├── requirements.txt                    # Pinned core dependencies
├── requirements-dashboard.txt          # Optional Streamlit UI dependencies
├── config/
│   ├── default.yaml                    # Full scale configuration (50,000 shipments, seed 20261022)
│   └── starter.yaml                    # Starter scale configuration (scale 0.01)
├── src/eta_data/
│   ├── __init__.py
│   ├── config.py                       # Configuration loader and scale calculator
│   ├── rng.py                          # SeedSequence-spawned decoupled per-entity streams
│   ├── ids.py                          # Immutable, zero-padded ID formatters + regex validators
│   ├── calendars.py                    # Operating hours, weekend/holiday logic, effective windows
│   ├── master/
│   │   ├── carriers.py                 # Multi-modal carriers and reliability tiers
│   │   ├── facilities.py               # Hubs, depots, warehouses, ports on 2D logistics plane
│   │   ├── service_levels.py           # Contractual SLAs (targets, grace hours, severe thresholds)
│   │   └── routes.py                   # Routes & RouteLegTemplates (1 to 4 hops)
│   ├── transactions/
│   │   ├── disruptions.py              # Disruption windows (weather + facility) & bridge tables
│   │   ├── shipments.py                # Shipment generator with business-hour seasonality
│   │   ├── simulation.py               # Core causal physics engine (carrier noise, weather, reroutes)
│   │   ├── queues.py                   # Periodic facility queue snapshots over time
│   │   └── events.py                   # Telemetry events, ingestion lag, duplicates, gaps
│   ├── labels.py                       # Delay labeling & exact arithmetic decomposition
│   ├── eta.py                          # Leakage-safe point-in-time ETA snapshot engine
│   ├── anomalies.py                    # Controlled edge-case injector with ground-truth isolation
│   ├── export.py                       # CSV, JSON, SQL seed script, SQLite DB, SHA-256 manifest
│   ├── validate.py                     # 12-suite validation engine (emits VALIDATION_REPORT.md)
│   └── evaluate.py                     # Temporal ML baseline evaluation & leakage trap demo
├── scripts/
│   ├── generate.py                     # Primary CLI pipeline entry point
│   └── repro_check.py                  # Dual-run bitwise SHA-256 check (emits REPRODUCIBILITY.md)
├── dashboard/
│   └── app.py                          # Interactive Streamlit operations & ML analytics cockpit
├── tests/
│   ├── test_ids.py                     # ID regex patterns and zero-padding format tests
│   ├── test_calendars.py               # Facility operating shifts and holiday closures
│   ├── test_master.py                  # Master entity generators and route templates
│   ├── test_disruptions.py             # Disruption windows, exact split, and queue snapshots
│   ├── test_simulation.py              # Causal transit times and leg sequencing
│   ├── test_events.py                  # Exact event count calibration and status history
│   ├── test_labels.py                  # Delay boundary conditions and arithmetic reconciliation
│   ├── test_eta_leakage.py             # Feature leakage cutoff tests
│   ├── test_anomalies.py               # Non-leakage test of ground truth columns
│   ├── test_validate.py                # In-memory validation suite execution
│   └── test_reproducibility.py         # In-process dual-generation checksum match
├── data/
│   ├── starter/                        # Small dataset committed to git (scale: 0.01)
│   └── full/                           # Generated locally (scale: 1.0, gitignored)
├── ground_truth/
│   ├── ground_truth.csv                # Isolated anomaly audit log (never leaks to features)
│   └── ground_truth.json
└── docs/
    ├── DATA_DICTIONARY.md              # Field-by-field definitions, units, and validation rules
    ├── schema.json                     # Machine-readable JSON schema
    ├── ER_DIAGRAM.md                   # Mermaid ER diagram and cardinality matrix
    ├── ASSUMPTIONS.md                  # Explicit assumptions log
    ├── DESIGN_DECISIONS.md             # Key architectural decisions and trade-offs
    ├── BUSINESS_RULES.md               # Simulation formulas with worked end-to-end example
    ├── VALIDATION_REPORT.md            # Generated validation report
    ├── REPRODUCIBILITY.md              # Generated dual-run bitwise verification report
    ├── EVALUATION.md                   # ML baseline comparison & leakage trap metrics
    ├── AI_USAGE.md                     # Disclosure of AI acceleration & human review
    └── SOURCE_MANIFEST.md             # 100% synthetic attribution and data governance
```

---

## 5. Key Design Decisions

1. **RNG Decoupling (`numpy.random.SeedSequence.spawn`)**: Partitioned independent generators prevent cross-domain random trajectory coupling. Adding or modifying an attribute in carriers does not alter facility coordinates or weather windows.
2. **Strict Ingestion-Time Cutoffs**: All feature generation uses `ingestion_time <= prediction_time`. We explicitly demonstrate the **leakage trap**, showing how using `event_time` creates an illusion of high predictive accuracy that fails in production.
3. **Exact Additive Delay Reconciliation**: Attributed delays (`WEATHER`, `FACILITY_QUEUE`, `CARRIER_DELAY`, `ROUTE_CHANGE`, `CALENDAR_CLOSURE`, `LATE_PICKUP`) arithmetically sum to total positive delay within $<10^{-6}$ hours.
4. **Ground-Truth Non-Leakage**: Anomaly labels exist exclusively in `ground_truth/`. Input tables (`shipments.csv`, `tracking_events.csv`) are 100% free of anomaly giveaway columns.

---

## 6. How I Know It Works

1. **Automated Validation (`python run.py validate`)**:
   - 12 independent check suites pass with 0 unlabelled violations.
   - Audits 100% of injected anomalies in `ground_truth/` with 100% precision and recall.
2. **Bitwise Reproducibility (`python run.py repro`)**:
   - Generates two completely independent runs from master seed `20261022` and verifies matching SHA-256 hashes across every file.
3. **SQLite Foreign Keys Enforced**:
   - Database loaded via `seed.sql` with `PRAGMA foreign_keys = ON;`.
   - `PRAGMA foreign_key_check;` returns `[]` (zero broken foreign keys).
4. **Pytest Coverage**:
   - 24 comprehensive unit and integration tests pass in $<2$ seconds (`pytest tests/`).

---

## 7. Known Limitations & Next Steps

1. **Flat Coordinate Plane**: Synthetic facilities are modeled on a continuous 2D Euclidean grid $[0, 1000] \times [0, 1000]$ with circuity multipliers rather than spherical WGS84 geodesics. Future iterations could incorporate real-world road networks (e.g. OpenStreetMap).
2. **Weather Envelopes**: Disruptions currently operate over regional bounding boxes with duration intervals. Future expansions could model continuous front-line storm vector trajectories.
3. **Dynamic Re-routing Depth**: The simulation currently executes single-hop detour reroutes. Multi-agent dynamic network flow optimization (e.g., flow conservation solvers) could model system-wide reroute cascades.

---

## 8. Author & Verification

- **Author**: YottaFlex AI Senior Data / ML Engineer Candidate
- **Generation Seed**: `20261022`
- **Simulation Epoch**: `2026-03-01T00:00:00Z` (90-day simulation window)
- **License**: MIT
