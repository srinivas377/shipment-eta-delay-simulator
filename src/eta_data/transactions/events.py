"""
Tracking event generation engine with realistic ingestion lag, telemetry gaps,
duplicate scanner retries, exact count calibration, and append-only status history.
"""

from __future__ import annotations

import heapq
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from eta_data.config import AppConfig
from eta_data.ids import (
    build_event_id,
    build_status_history_id,
)
from eta_data.rng import RNGManager

SOURCE_SYSTEMS = ["MOBILE_SCANNER", "PORTAL", "EDI_214", "GPS_TELEMATICS"]


def _draw_ingestion_lag_hours(rng: Any, lag_cfg: Dict[str, Any]) -> float:
    """Draws ingestion lag from 3-component mixture distribution."""
    p = float(rng.random())
    if p < 0.82:
        # Real-time cellular / IoT
        shape = 2.0
        scale = 0.15  # ~0.3 hours (18 min)
        return float(rng.gamma(shape, scale))
    elif p < 0.97:
        # Batch dock upload
        return float(rng.lognormal(1.2, 0.6))
    else:
        # Long tail / remote dead zone sync
        return float(rng.exponential(18.0))


def generate_tracking_events(
    cfg: AppConfig,
    shipments: List[Dict[str, Any]],
    legs: List[Dict[str, Any]],
    route_changes: List[Dict[str, Any]],
    rng_manager: RNGManager,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Generates tracking events, applies ingestion lag, creates duplicates and gaps,
    calibrates to exactly cfg.targets.target_events, and emits ShipmentStatusHistory.
    """
    rng_events = rng_manager.get_stream("events_lifecycle")
    rng_lag = rng_manager.get_stream("events_ingestion_lag")
    rng_dup = rng_manager.get_stream("events_duplicates")

    target_total_events = cfg.targets.target_events

    # Group legs by shipment_id
    legs_by_shipment: Dict[str, List[Dict[str, Any]]] = {}
    for l in legs:
        legs_by_shipment.setdefault(l["shipment_id"], []).append(l)
    for shp_id in legs_by_shipment:
        legs_by_shipment[shp_id].sort(key=lambda x: x["leg_sequence"])

    # Group route changes by shipment_id
    rtc_by_shipment: Dict[str, List[Dict[str, Any]]] = {}
    for r in route_changes:
        rtc_by_shipment.setdefault(r["shipment_id"], []).append(r)

    raw_events_by_shp: Dict[str, List[Dict[str, Any]]] = {}

    for shp in shipments:
        shp_id = shp["shipment_id"]
        shp_events: List[Dict[str, Any]] = []

        # 1. CREATED
        t_create = datetime.fromisoformat(shp["created_at"].rstrip("Z"))
        lag = _draw_ingestion_lag_hours(rng_lag, cfg.ingestion_lag)
        shp_events.append({
            "shipment_id": shp_id,
            "leg_id": None,
            "facility_id": shp["origin_facility_id"],
            "event_type": "CREATED",
            "event_time_dt": t_create,
            "ingestion_time_dt": t_create + timedelta(hours=lag),
            "source_system": "PORTAL",
            "is_duplicate": False,
        })

        shp_legs = legs_by_shipment.get(shp_id, [])
        if shp_legs:
            # 2. PICKED_UP at Leg 1 departure
            first_leg = shp_legs[0]
            t_pickup = datetime.fromisoformat(first_leg["actual_depart_at"].rstrip("Z"))
            lag = _draw_ingestion_lag_hours(rng_lag, cfg.ingestion_lag)
            shp_events.append({
                "shipment_id": shp_id,
                "leg_id": first_leg["leg_id"],
                "facility_id": first_leg["from_facility_id"],
                "event_type": "PICKED_UP",
                "event_time_dt": t_pickup,
                "ingestion_time_dt": t_pickup + timedelta(hours=lag),
                "source_system": "MOBILE_SCANNER",
                "is_duplicate": False,
            })

            # Check for route change event
            if shp_id in rtc_by_shipment:
                for rtc in rtc_by_shipment[shp_id]:
                    t_rtc = datetime.fromisoformat(rtc["effective_time"].rstrip("Z"))
                    lag = _draw_ingestion_lag_hours(rng_lag, cfg.ingestion_lag)
                    shp_events.append({
                        "shipment_id": shp_id,
                        "leg_id": first_leg["leg_id"],
                        "facility_id": None,
                        "event_type": "ROUTE_CHANGED",
                        "event_time_dt": t_rtc,
                        "ingestion_time_dt": t_rtc + timedelta(hours=lag),
                        "source_system": "PORTAL",
                        "is_duplicate": False,
                    })

            for leg in shp_legs:
                t_dep = datetime.fromisoformat(leg["actual_depart_at"].rstrip("Z"))
                t_arr = datetime.fromisoformat(leg["actual_arrive_at"].rstrip("Z"))

                # DEPARTED
                lag = _draw_ingestion_lag_hours(rng_lag, cfg.ingestion_lag)
                shp_events.append({
                    "shipment_id": shp_id,
                    "leg_id": leg["leg_id"],
                    "facility_id": leg["from_facility_id"],
                    "event_type": "DEPARTED",
                    "event_time_dt": t_dep,
                    "ingestion_time_dt": t_dep + timedelta(hours=lag),
                    "source_system": "GPS_TELEMATICS",
                    "is_duplicate": False,
                })

                # Telemetry gap: 1.5% chance to drop ARRIVED scan
                if rng_events.random() >= 0.015:
                    lag = _draw_ingestion_lag_hours(rng_lag, cfg.ingestion_lag)
                    shp_events.append({
                        "shipment_id": shp_id,
                        "leg_id": leg["leg_id"],
                        "facility_id": leg["to_facility_id"],
                        "event_type": "ARRIVED",
                        "event_time_dt": t_arr,
                        "ingestion_time_dt": t_arr + timedelta(hours=lag),
                        "source_system": "MOBILE_SCANNER",
                        "is_duplicate": False,
                    })

            # OUT_FOR_DELIVERY & DELIVERED
            if shp.get("actual_delivery_at"):
                t_del = datetime.fromisoformat(shp["actual_delivery_at"].rstrip("Z"))
                t_out = max(t_arr, t_del - timedelta(hours=1.0))
                lag = _draw_ingestion_lag_hours(rng_lag, cfg.ingestion_lag)
                shp_events.append({
                    "shipment_id": shp_id,
                    "leg_id": shp_legs[-1]["leg_id"],
                    "facility_id": shp["destination_facility_id"],
                    "event_type": "OUT_FOR_DELIVERY",
                    "event_time_dt": t_out,
                    "ingestion_time_dt": t_out + timedelta(hours=lag),
                    "source_system": "MOBILE_SCANNER",
                    "is_duplicate": False,
                })

                lag = _draw_ingestion_lag_hours(rng_lag, cfg.ingestion_lag)
                shp_events.append({
                    "shipment_id": shp_id,
                    "leg_id": shp_legs[-1]["leg_id"],
                    "facility_id": shp["destination_facility_id"],
                    "event_type": "DELIVERED",
                    "event_time_dt": t_del,
                    "ingestion_time_dt": t_del + timedelta(hours=lag),
                    "source_system": "MOBILE_SCANNER",
                    "is_duplicate": False,
                })

        raw_events_by_shp[shp_id] = shp_events

    # Count current base events
    current_count = sum(len(evts) for evts in raw_events_by_shp.values())

    # Calibration Phase: deterministically hit EXACT target_total_events
    if current_count < target_total_events:
        needed = target_total_events - current_count
        # Deterministically allocate additional IN_TRANSIT_SCAN and retry DUPLICATE events
        # using a round-robin across shipments
        shp_ids = sorted(raw_events_by_shp.keys())
        alloc_idx = 0
        while needed > 0:
            s_id = shp_ids[alloc_idx % len(shp_ids)]
            ev_list = raw_events_by_shp[s_id]
            # Find candidate leg to inject transit scan
            shp_legs = legs_by_shipment.get(s_id, [])
            if shp_legs:
                target_leg = shp_legs[(alloc_idx // len(shp_ids)) % len(shp_legs)]
                t_dep = datetime.fromisoformat(target_leg["actual_depart_at"].rstrip("Z"))
                t_arr = datetime.fromisoformat(target_leg["actual_arrive_at"].rstrip("Z"))
                mid_time = t_dep + (t_arr - t_dep) * float(rng_events.uniform(0.3, 0.7))
                lag = _draw_ingestion_lag_hours(rng_lag, cfg.ingestion_lag)

                # 70% in-transit waypoint scan, 30% duplicate retry scan
                if rng_dup.random() < 0.70:
                    ev_list.append({
                        "shipment_id": s_id,
                        "leg_id": target_leg["leg_id"],
                        "facility_id": None,
                        "event_type": "IN_TRANSIT_SCAN",
                        "event_time_dt": mid_time,
                        "ingestion_time_dt": mid_time + timedelta(hours=lag),
                        "source_system": "GPS_TELEMATICS",
                        "is_duplicate": False,
                    })
                else:
                    # Duplicate retry scan of departure
                    ev_list.append({
                        "shipment_id": s_id,
                        "leg_id": target_leg["leg_id"],
                        "facility_id": target_leg["from_facility_id"],
                        "event_type": "DEPARTED",
                        "event_time_dt": t_dep,
                        "ingestion_time_dt": t_dep + timedelta(hours=lag + 0.1),
                        "source_system": "GPS_TELEMATICS",
                        "is_duplicate": True,
                    })
                needed -= 1
            alloc_idx += 1
    elif current_count > target_total_events:
        # Prune non-terminal scans deterministically
        excess = current_count - target_total_events
        shp_ids = sorted(raw_events_by_shp.keys(), reverse=True)
        alloc_idx = 0
        while excess > 0:
            s_id = shp_ids[alloc_idx % len(shp_ids)]
            ev_list = raw_events_by_shp[s_id]
            # Drop non-essential intermediate scan if possible
            for i in range(len(ev_list) - 1, -1, -1):
                if ev_list[i]["event_type"] in ("IN_TRANSIT_SCAN", "ARRIVED"):
                    ev_list.pop(i)
                    excess -= 1
                    break
            alloc_idx += 1

    # Finalize Sequence Numbers, IDs, and ShipmentStatusHistory
    all_final_events: List[Dict[str, Any]] = []
    status_history_records: List[Dict[str, Any]] = []
    ssh_seq = 1

    for s_id in sorted(raw_events_by_shp.keys()):
        ev_list = raw_events_by_shp[s_id]
        # Sort chronologically by event_time_dt
        ev_list.sort(key=lambda x: (x["event_time_dt"], x["is_duplicate"]))

        first_event_of_type: Dict[str, str] = {}
        prev_status = None

        for seq_idx, ev in enumerate(ev_list, start=1):
            event_id = build_event_id(s_id, seq_idx)
            is_dup = ev["is_duplicate"]
            dup_of = None
            if is_dup:
                dup_of = first_event_of_type.get(ev["event_type"])
            else:
                first_event_of_type[ev["event_type"]] = event_id

            final_ev = {
                "event_id": event_id,
                "shipment_id": s_id,
                "leg_id": ev["leg_id"],
                "facility_id": ev["facility_id"],
                "event_type": ev["event_type"],
                "event_time": ev["event_time_dt"].isoformat() + "Z",
                "ingestion_time": ev["ingestion_time_dt"].isoformat() + "Z",
                "source_system": ev["source_system"],
                "is_duplicate_of": dup_of,
                "sequence_no": seq_idx,
            }
            all_final_events.append(final_ev)

            # Map event to shipment lifecycle status
            new_status = None
            if ev["event_type"] == "CREATED":
                new_status = "CREATED"
            elif ev["event_type"] in ("PICKED_UP", "DEPARTED", "IN_TRANSIT_SCAN"):
                new_status = "IN_TRANSIT"
            elif ev["event_type"] == "DELIVERED":
                new_status = "DELIVERED"

            if new_status and new_status != prev_status:
                ssh_row = {
                    "history_id": build_status_history_id(ssh_seq),
                    "shipment_id": s_id,
                    "status": new_status,
                    "transition_time": ev["event_time_dt"].isoformat() + "Z",
                    "trigger_event_id": event_id,
                }
                status_history_records.append(ssh_row)
                ssh_seq += 1
                prev_status = new_status

    return all_final_events, status_history_records
