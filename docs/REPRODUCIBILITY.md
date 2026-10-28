# Reproducibility Verification Report

**Audit Timestamp**: 2026-10-28T09:52:24.494206Z  
**Master Seed**: `20261022`  
**Scale**: `0.01`  
**Run 1 Execution Time**: 0.55s  
**Run 2 Execution Time**: 0.58s  
**Overall Status**: BIT-FOR-BIT IDENTICAL (100% REPRODUCIBLE)  

---

## Dual-Run Bitwise Comparison

| File Name | Run 1 Rows | Run 2 Rows | SHA-256 Checksum (Run 1) | SHA-256 Match | Verification Status |
|---|---|---|---|---|---|
| `carrier_calendars.csv` | 42 | 42 | `93f19547c7a14c10...` | MATCH | IDENTICAL |
| `carriers.csv` | 6 | 6 | `ee5da8ec331a70bd...` | MATCH | IDENTICAL |
| `delay_reasons.csv` | 6 | 6 | `7bc5b20ea22a32b5...` | MATCH | IDENTICAL |
| `eta_estimates.csv` | 5013 | 5013 | `448cc27bcc12d092...` | MATCH | IDENTICAL |
| `facilities.csv` | 10 | 10 | `39050154826fbcdf...` | MATCH | IDENTICAL |
| `facility_calendars.csv` | 70 | 70 | `bd070dd7edb48226...` | MATCH | IDENTICAL |
| `facility_queues.csv` | 300 | 300 | `fae2d750f1e2ae4d...` | MATCH | IDENTICAL |
| `ground_truth.csv` | 50 | 50 | `860799bf99bbf555...` | MATCH | IDENTICAL |
| `ground_truth.json` | 50 | 50 | `c82b522cbaf6d4d7...` | MATCH | IDENTICAL |
| `logistics.sqlite` | 11991 | 11991 | `8e85c741541ec0a7...` | MATCH | IDENTICAL |
| `route_changes.csv` | 23 | 23 | `e517e54f4f9cbd34...` | MATCH | IDENTICAL |
| `route_leg_templates.csv` | 30 | 30 | `2310ab0af7a7cd80...` | MATCH | IDENTICAL |
| `routes.csv` | 15 | 15 | `94cd35fb6a6a3cf1...` | MATCH | IDENTICAL |
| `seed.sql` | 11991 | 11991 | `893673fbc1e93345...` | MATCH | IDENTICAL |
| `service_levels.csv` | 4 | 4 | `899adc043272de6a...` | MATCH | IDENTICAL |
| `shipment_delay_reasons.csv` | 329 | 329 | `a7ef26683fb2022a...` | MATCH | IDENTICAL |
| `shipment_legs.csv` | 987 | 987 | `ea0a31659b19261d...` | MATCH | IDENTICAL |
| `shipment_status_history.csv` | 1500 | 1500 | `9fc8f81d243529d5...` | MATCH | IDENTICAL |
| `shipments.csv` | 500 | 500 | `ea5e3e2bec387934...` | MATCH | IDENTICAL |
| `tracking_events.csv` | 3000 | 3000 | `d5ece7f1245b07d8...` | MATCH | IDENTICAL |
| `weather_event_facilities.csv` | 18 | 18 | `b36d2318024b9c16...` | MATCH | IDENTICAL |
| `weather_event_legs.csv` | 128 | 128 | `eb41ec88dd190feb...` | MATCH | IDENTICAL |
| `weather_events.csv` | 10 | 10 | `dcd9f8a9411a7148...` | MATCH | IDENTICAL |

---

## Technical Safeguards for Determinism

1. **Independent RNG Streams**: Master seed `20261022` is partitioned using `numpy.random.SeedSequence.spawn`, ensuring modifications to one entity generator never shuffle the random trajectory of others.
2. **Zero System-Clock Dependencies**: No non-deterministic `datetime.now()` calls exist in generation logic. Timestamps derive from a static epoch (`2026-03-01T00:00:00Z`).
3. **Stable Sorting**: Tables are explicitly sorted across composite primary keys prior to export, preventing unordered dictionary/set nondeterminism across runs or platforms.
4. **No Python hash() Iteration**: Set lookups avoid Python's randomized hash seed (`PYTHONHASHSEED`).