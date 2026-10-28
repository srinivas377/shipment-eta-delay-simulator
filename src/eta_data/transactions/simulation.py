"""
Core causal physics and operational logistics simulation engine.
Calculates planned and actual leg transit times, carrier noise, weather impact,
facility queue waits, calendar closures, and dynamic reroutes.
"""

from __future__ import annotations

import math
from datetime import datetime, timedelta
from typing import Any, Dict, List, Tuple
from eta_data.calendars import get_next_open_time
from eta_data.config import AppConfig
from eta_data.ids import (
    build_leg_id,
    build_route_change_id,
)
from eta_data.rng import RNGManager

# Carrier tier distribution parameters: (mu, sigma)
TIER_PARAMS = {
    "TIER_1": (-0.005, 0.05),
    "TIER_2": (0.015, 0.12),
    "TIER_3": (0.050, 0.22),
}


class SimulationEngine:
    """Executes the deterministic causal simulation across shipments and legs."""

    def __init__(
        self,
        cfg: AppConfig,
        facilities: List[Dict[str, Any]],
        carriers: List[Dict[str, Any]],
        routes: List[Dict[str, Any]],
        templates: List[Dict[str, Any]],
        disruptions: List[Dict[str, Any]],
        rng_manager: RNGManager,
    ) -> None:
        self.cfg = cfg
        self.facilities = {f["facility_id"]: f for f in facilities}
        self.carriers = {c["carrier_id"]: c for c in carriers}
        self.routes = {r["route_id"]: r for r in routes}
        self.templates_by_route: Dict[str, List[Dict[str, Any]]] = {}
        for t in templates:
            self.templates_by_route.setdefault(t["route_id"], []).append(t)
        # Sort templates by leg sequence
        for r_id in self.templates_by_route:
            self.templates_by_route[r_id].sort(key=lambda x: x["leg_sequence"])

        self.disruptions = disruptions
        self.rng_transit = rng_manager.get_stream("simulation_transit")
        self.rng_reroute = rng_manager.get_stream("reroute_decisions")

        # Precompute disruption intervals by region
        self.disruptions_by_region: Dict[str, List[Tuple[Dict[str, Any], datetime, datetime]]] = {}
        for d in disruptions:
            t_start = datetime.fromisoformat(d["start_time"].rstrip("Z"))
            t_end = datetime.fromisoformat(d["end_time"].rstrip("Z"))
            self.disruptions_by_region.setdefault(d["region"], []).append((d, t_start, t_end))

    def _get_weather_multiplier(
        self,
        region: str,
        depart_dt: datetime,
        planned_hours: float,
    ) -> Tuple[float, float]:
        """
        Calculates weather speed multiplier and overlapping disruption hours.
        Returns (multiplier, weather_delay_hours).
        """
        regional_disruptions = self.disruptions_by_region.get(region, [])
        if not regional_disruptions:
            return 1.0, 0.0

        est_arrive_dt = depart_dt + timedelta(hours=planned_hours)
        compound_mult = 1.0
        weather_delay = 0.0

        for d, d_start, d_end in regional_disruptions:
            if d["window_type"] != "WEATHER":
                continue
            # Check overlap
            overlap_start = max(depart_dt, d_start)
            overlap_end = min(est_arrive_dt, d_end)
            if overlap_start < overlap_end:
                overlap_hours = (overlap_end - overlap_start).total_seconds() / 3600.0
                mult = float(d["speed_multiplier"])
                weight = min(1.0, overlap_hours / max(1.0, planned_hours))
                added = (mult - 1.0) * weight
                compound_mult += added
                weather_delay += planned_hours * added

        return max(1.0, round(compound_mult, 3)), max(0.0, round(weather_delay, 2))

    def simulate(
        self,
        shipments: List[Dict[str, Any]],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Simulates all shipments, generating ShipmentLeg and RouteChange records.
        Updates shipment actual_delivery_at and is_rerouted fields in-place.
        """
        all_legs: List[Dict[str, Any]] = []
        all_route_changes: List[Dict[str, Any]] = []
        rtc_seq = 1

        for shp in shipments:
            shp_id = shp["shipment_id"]
            created_dt = datetime.fromisoformat(shp["created_at"].rstrip("Z"))
            orig_fac = self.facilities[shp["origin_facility_id"]]

            # Pickup scheduling: respect origin opening hours and supplier prep delay
            if self.rng_transit.random() < 0.22:
                # 22% of shipments experience supplier dispatch staging delay
                dispatch_prep = float(self.rng_transit.uniform(3.0, 12.0))
            else:
                dispatch_prep = float(self.rng_transit.uniform(0.5, 2.5))
            earliest_pickup = created_dt + timedelta(hours=dispatch_prep)
            actual_pickup = get_next_open_time(orig_fac["type"], earliest_pickup)

            route_templates = self.templates_by_route.get(shp["route_id"], [])
            current_depart_dt = actual_pickup
            planned_cursor_dt = earliest_pickup

            shipment_legs: List[Dict[str, Any]] = []
            is_rerouted = False

            leg_idx = 0
            while leg_idx < len(route_templates):
                tmpl = route_templates[leg_idx]
                leg_seq = len(shipment_legs) + 1
                leg_id = build_leg_id(shp_id, leg_seq)

                from_fac = self.facilities[tmpl["from_facility_id"]]
                to_fac = self.facilities[tmpl["to_facility_id"]]
                carrier = self.carriers[tmpl["carrier_id"]]
                planned_duration = float(tmpl["planned_duration_hours"])

                # Planned timestamps
                planned_dep = planned_cursor_dt
                planned_arr = planned_dep + timedelta(hours=planned_duration)
                planned_cursor_dt = planned_arr + timedelta(hours=1.0)  # dwell buffer

                # Carrier noise
                tier = carrier["reliability_tier"]
                mu, sigma = TIER_PARAMS[tier]
                carrier_noise = float(self.rng_transit.lognormal(mu, sigma))

                # Weather impact along leg region
                leg_region = to_fac["region"]
                weather_mult, wx_delay = self._get_weather_multiplier(
                    leg_region, current_depart_dt, planned_duration
                )

                # Check reroute condition at intermediate hub
                if (
                    leg_idx > 0
                    and leg_idx < len(route_templates) - 1
                    and not is_rerouted
                    and (weather_mult > 1.35 or self.rng_reroute.random() < 0.05)
                ):
                    # Trigger reroute detour
                    is_rerouted = True
                    shp["is_rerouted"] = True

                    # Find alternate route
                    alt_routes = [
                        r for r in self.routes.values()
                        if r["destination_facility_id"] == shp["destination_facility_id"]
                        and r["route_id"] != shp["route_id"]
                    ]
                    if alt_routes:
                        new_route = self.rng_reroute.choice(alt_routes)
                        rtc_row = {
                            "change_id": build_route_change_id(rtc_seq),
                            "shipment_id": shp_id,
                            "old_route_id": shp["route_id"],
                            "new_route_id": new_route["route_id"],
                            "reason": "WEATHER_CONGESTION_DETOUR",
                            "effective_time": current_depart_dt.isoformat() + "Z",
                        }
                        all_route_changes.append(rtc_row)
                        rtc_seq += 1

                # Actual transit calculation
                actual_duration = max(0.2, planned_duration * carrier_noise * weather_mult)
                actual_arr = current_depart_dt + timedelta(hours=actual_duration)

                leg_row = {
                    "leg_id": leg_id,
                    "shipment_id": shp_id,
                    "leg_sequence": leg_seq,
                    "from_facility_id": from_fac["facility_id"],
                    "to_facility_id": to_fac["facility_id"],
                    "carrier_id": carrier["carrier_id"],
                    "planned_depart_at": planned_dep.isoformat() + "Z",
                    "planned_arrive_at": planned_arr.isoformat() + "Z",
                    "actual_depart_at": current_depart_dt.isoformat() + "Z",
                    "actual_arrive_at": actual_arr.isoformat() + "Z",
                    "leg_status": "COMPLETED",
                }
                shipment_legs.append(leg_row)
                all_legs.append(leg_row)

                # Advance to next leg: intermediate facility queue and calendar
                if leg_idx < len(route_templates) - 1:
                    base_dwell = float(to_fac.get("dwell_hours", 1.5))
                    queue_factor = float(self.rng_transit.uniform(0.2, 1.8))
                    facility_wait = base_dwell * queue_factor

                    earliest_next_dep = actual_arr + timedelta(hours=facility_wait)
                    next_open_dep = get_next_open_time(to_fac["type"], earliest_next_dep)
                    current_depart_dt = next_open_dep
                else:
                    # Final destination reached
                    final_handling = float(self.rng_transit.uniform(0.5, 1.5))
                    delivery_dt = actual_arr + timedelta(hours=final_handling)
                    shp["actual_delivery_at"] = delivery_dt.isoformat() + "Z"
                    shp["current_status"] = "DELIVERED"

                leg_idx += 1

        return all_legs, all_route_changes
