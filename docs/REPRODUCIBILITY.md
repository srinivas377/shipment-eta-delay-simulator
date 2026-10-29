# Reproducibility Verification Report

**Audit Timestamp**: 2026-10-28T17:23:36.560207+00:00  
**Master Seed**: `20261022`  
**Scale**: `0.01`  
**Run 1 Execution Time**: 0.69s  
**Run 2 Execution Time**: 0.72s  
**Overall Status**: BIT-FOR-BIT IDENTICAL (100% REPRODUCIBLE)  

---

## Dual-Run Bitwise Comparison

| File Name | Run 1 Rows | Run 2 Rows | SHA-256 Checksum (Run 1) | SHA-256 Match | Verification Status |
|---|---|---|---|---|---|
| `carrier_calendars.csv` | 42 | 42 | `b35425f7bdd77873...` | MATCH | IDENTICAL |
| `carriers.csv` | 6 | 6 | `dbd66f3cb53ba3d8...` | MATCH | IDENTICAL |
| `delay_reasons.csv` | 6 | 6 | `ce1b06477adb5900...` | MATCH | IDENTICAL |
| `eta_estimates.csv` | 7242 | 7242 | `940668634a079b73...` | MATCH | IDENTICAL |
| `facilities.csv` | 10 | 10 | `a40b5f4ab69a46f6...` | MATCH | IDENTICAL |
| `facility_calendars.csv` | 70 | 70 | `aed16aab3530004d...` | MATCH | IDENTICAL |
| `facility_queues.csv` | 300 | 300 | `bc6198bea7e339b8...` | MATCH | IDENTICAL |
| `ground_truth.csv` | 67 | 67 | `bba840b6e90f01ca...` | MATCH | IDENTICAL |
| `ground_truth.json` | 67 | 67 | `83cd6e98d83b984b...` | MATCH | IDENTICAL |
| `logistics.sqlite` | 14519 | 14519 | `dc96f5699581cac0...` | MATCH | IDENTICAL |
| `route_changes.csv` | 15 | 15 | `fdb9853925033c87...` | MATCH | IDENTICAL |
| `route_leg_templates.csv` | 31 | 31 | `8b5ce7c1d72e32ad...` | MATCH | IDENTICAL |
| `routes.csv` | 15 | 15 | `a9a5ce56f7016e71...` | MATCH | IDENTICAL |
| `seed.sql` | 14519 | 14519 | `bf8db70816fcd58b...` | MATCH | IDENTICAL |
| `service_levels.csv` | 4 | 4 | `9db727f3f5e84980...` | MATCH | IDENTICAL |
| `shipment_delay_reasons.csv` | 596 | 596 | `35073a170bf502b1...` | MATCH | IDENTICAL |
| `shipment_legs.csv` | 1009 | 1009 | `c6cf82c52e7fcddc...` | MATCH | IDENTICAL |
| `shipment_status_history.csv` | 1500 | 1500 | `ce83dfcd68e98fa8...` | MATCH | IDENTICAL |
| `shipments.csv` | 500 | 500 | `d9669f626563980a...` | MATCH | IDENTICAL |
| `tracking_events.csv` | 3000 | 3000 | `811799c047903a0c...` | MATCH | IDENTICAL |
| `weather_event_facilities.csv` | 18 | 18 | `8c826c0bdd8cd20c...` | MATCH | IDENTICAL |
| `weather_event_legs.csv` | 145 | 145 | `ca9bc2af26c2ab53...` | MATCH | IDENTICAL |
| `weather_events.csv` | 10 | 10 | `5f0345c2fe519d84...` | MATCH | IDENTICAL |

---

## Technical Safeguards for Determinism

1. **Independent RNG Streams**: Master seed `20261022` is partitioned using `numpy.random.SeedSequence.spawn`, ensuring modifications to one entity generator never shuffle the random trajectory of others.
2. **Zero System-Clock Dependencies**: No non-deterministic `datetime.now()` calls exist in generation logic. Timestamps derive from a static epoch (`2026-03-01T00:00:00Z`).
3. **Stable Sorting**: Tables are explicitly sorted across composite primary keys prior to export, preventing unordered dictionary/set nondeterminism across runs or platforms.
4. **No Python hash() Iteration**: Set lookups avoid Python's randomized hash seed (`PYTHONHASHSEED`).