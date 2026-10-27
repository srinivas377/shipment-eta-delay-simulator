"""Deterministic Shipment generator with realistic pickup seasonality."""

from __future__ import annotations

import math
from datetime import datetime, timedelta
from typing import Any, Dict, List
from eta_data.config import AppConfig
from eta_data.ids import build_shipment_id
from eta_data.rng import RNGManager


def generate_shipments(
    cfg: AppConfig,
    routes: List[Dict[str, Any]],
    service_levels: List[Dict[str, Any]],
    rng_manager: RNGManager,
) -> List[Dict[str, Any]]:
    """
    Generates core Shipment rows with service level selection, route assignment,
    and business-hour creation seasonality.
    """
    rng = rng_manager.get_stream("shipment_generation")
    start_dt = datetime.fromisoformat(cfg.simulation.start_date.rstrip("Z"))
    duration_days = cfg.simulation.duration_days
    num_shipments = cfg.targets.num_shipments

    sl_weights = [sl.get("weight", 0.25) for sl in cfg.master_data.get("service_levels", [])]
    if len(sl_weights) != len(service_levels) or sum(sl_weights) == 0:
        sl_weights = [1.0 / len(service_levels)] * len(service_levels)
    else:
        tot = sum(sl_weights)
        sl_weights = [w / tot for w in sl_weights]

    shipments: List[Dict[str, Any]] = []

    for idx in range(num_shipments):
        shp_id = build_shipment_id(idx + 1)
        supplier_id = f"SUP-{int(rng.integers(1, 51)):03d}"

        # Route assignment
        route = rng.choice(routes)
        sl = rng.choice(service_levels, p=sl_weights)

        # Realistic creation time: business hours (08:00 - 18:00) with weekday skew
        day_offset = int(rng.integers(0, max(1, duration_days - 7)))
        dow = (start_dt + timedelta(days=day_offset)).weekday()

        # Hour drawn from beta distribution peaked around 11:00 - 15:00
        hour_frac = rng.beta(2.5, 2.0)
        hour = int(7 + hour_frac * 12)  # 07:00 to 19:00
        minute = int(rng.integers(0, 60))
        second = int(rng.integers(0, 60))

        created_dt = start_dt + timedelta(days=day_offset, hours=hour, minutes=minute, seconds=second)
        target_hours = int(sl["target_hours"])
        promised_dt = created_dt + timedelta(hours=target_hours)

        shp_row = {
            "shipment_id": shp_id,
            "supplier_id": supplier_id,
            "origin_facility_id": route["origin_facility_id"],
            "destination_facility_id": route["destination_facility_id"],
            "service_level_id": sl["service_level_id"],
            "route_id": route["route_id"],
            "created_at": created_dt.isoformat() + "Z",
            "promised_delivery_at": promised_dt.isoformat() + "Z",
            "actual_delivery_at": None,  # Derived during simulation
            "current_status": "CREATED",
            "final_delay_label": "ON_TIME",  # Derived during labeling
            "is_rerouted": False,
        }
        shipments.append(shp_row)

    return shipments
