"""
YottaFlex AI Logistics Operations & ML Analytics Dashboard.
Interactive Streamlit web application providing executive KPIs, shipment timelines,
facility queue heatmaps, data quality audits, and operations exception cockpit.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import streamlit as st

# Set page configuration
st.set_page_config(
    page_title="YottaFlex AI | Logistics Telematics & ETA Analytics",
    page_icon="🚚",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Premium Styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    .main-header {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%);
        padding: 24px 32px;
        border-radius: 14px;
        margin-bottom: 24px;
        border: 1px solid rgba(255, 255, 255, 0.08);
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3);
    }
    
    .metric-card {
        background: #1e293b;
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 12px;
        padding: 18px 22px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    .metric-card:hover {
        border-color: #38bdf8;
        transform: translateY(-2px);
    }
    
    .badge-ontime {
        background-color: rgba(16, 185, 129, 0.2);
        color: #10b981;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .badge-delayed {
        background-color: rgba(245, 158, 11, 0.2);
        color: #f59e0b;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .badge-severe {
        background-color: rgba(239, 68, 68, 0.2);
        color: #ef4444;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.85rem;
    }
</style>
""", unsafe_allow_html=True)


ROOT = Path(__file__).resolve().parent.parent


@st.cache_resource
def get_db_connection(data_dir: Path) -> sqlite3.Connection:
    sqlite_path = data_dir / "logistics.sqlite"
    if not sqlite_path.exists():
        st.error(f"Database not found at {sqlite_path}. Please generate data first!")
        st.stop()
    conn = sqlite3.connect(sqlite_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def load_query(conn: sqlite3.Connection, query: str, params: tuple = ()) -> pd.DataFrame:
    return pd.read_sql_query(query, conn, params=params)


# Sidebar configuration
st.sidebar.image("https://img.icons8.com/isometric/100/delivery.png", width=64)
st.sidebar.title("YottaFlex AI")
st.sidebar.caption("Deterministic Logistics & ETA Synthetic Intelligence")

data_source = st.sidebar.radio(
    "Dataset Source",
    ["Starter Scale (500 Shipments)", "Full Scale (50,000 Shipments)"],
    index=0,
)

target_dir = ROOT / "data" / "starter" if "Starter" in data_source else ROOT / "data" / "full"

if not target_dir.exists():
    st.sidebar.warning(f"Dataset path `{target_dir.name}` does not exist yet. Please generate it using `python run.py full`.")
    target_dir = ROOT / "data" / "starter"

conn = get_db_connection(target_dir)

# Header
st.markdown("""
<div class="main-header">
    <div style="display: flex; justify-content: space-between; align-items: center;">
        <div>
            <h1 style="color: #f8fafc; margin: 0; font-size: 1.85rem; font-weight: 700;">
                Logistics Operations & ETA Intelligence Cockpit
            </h1>
            <p style="color: #94a3b8; margin: 6px 0 0 0; font-size: 0.95rem;">
                Causal Synthetic Telematics, Ingestion Lag Analytics, and Leakage-Safe Prediction Benchmarks
            </p>
        </div>
        <div>
            <span style="background: #0284c7; color: white; padding: 6px 14px; border-radius: 20px; font-size: 0.82rem; font-weight: 600; letter-spacing: 0.5px;">
                ENGINE V1.0.0
            </span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Navigation tabs
tabs = st.tabs([
    "📊 Executive KPIs",
    "🔍 Shipment Explorer & Timeline",
    "🏭 Facility Queues & Congestion",
    "🛡️ Data Quality & Anomaly Audit",
    "🚨 Operations Exception Cockpit",
])

# TAB 1: EXECUTIVE KPIS
with tabs[0]:
    st.subheader("Network Executive Overview")

    col1, col2, col3, col4, col5 = st.columns(5)
    
    total_shp = load_query(conn, "SELECT COUNT(*) as cnt FROM shipments")["cnt"][0]
    total_events = load_query(conn, "SELECT COUNT(*) as cnt FROM tracking_events")["cnt"][0]
    ontime_cnt = load_query(conn, "SELECT COUNT(*) as cnt FROM shipments WHERE final_delay_label='ON_TIME'")["cnt"][0]
    ontime_pct = round((ontime_cnt / total_shp) * 100, 1) if total_shp > 0 else 0
    severe_cnt = load_query(conn, "SELECT COUNT(*) as cnt FROM shipments WHERE final_delay_label='SEVERELY_DELAYED'")["cnt"][0]
    rerouted_cnt = load_query(conn, "SELECT COUNT(*) as cnt FROM shipments WHERE is_rerouted=1")["cnt"][0]

    with col1:
        st.metric("Total Shipments", f"{total_shp:,}")
    with col2:
        st.metric("Tracking Events", f"{total_events:,}")
    with col3:
        st.metric("On-Time SLA %", f"{ontime_pct}%", delta=f"{ontime_pct - 85.0:.1f}% vs Target")
    with col4:
        st.metric("Severely Delayed", f"{severe_cnt:,}")
    with col5:
        st.metric("Dynamic Reroutes", f"{rerouted_cnt:,}")

    st.markdown("---")
    
    c_left, c_right = st.columns([1, 1])

    with c_left:
        st.markdown("##### Delivery SLA Compliance Distribution")
        sla_df = load_query(conn, """
            SELECT final_delay_label as status, COUNT(*) as count 
            FROM shipments 
            GROUP BY final_delay_label
        """)
        st.bar_chart(sla_df.set_index("status"), color="#0284c7")

    with c_right:
        st.markdown("##### Delay Attribution Decomposition (Hours Attributed)")
        delay_reason_df = load_query(conn, """
            SELECT dr.reason_code, ROUND(SUM(sdr.delay_hours_attributed), 1) as total_hours
            FROM shipment_delay_reasons sdr
            JOIN delay_reasons dr ON sdr.delay_id = dr.delay_id
            GROUP BY dr.reason_code
            ORDER BY total_hours DESC
        """)
        st.bar_chart(delay_reason_df.set_index("reason_code"), color="#f59e0b")

    st.markdown("##### Mode Distribution & Carrier Reliability")
    carrier_df = load_query(conn, """
        SELECT c.mode, c.reliability_tier, COUNT(sl.leg_id) as executed_legs
        FROM shipment_legs sl
        JOIN carriers c ON sl.carrier_id = c.carrier_id
        GROUP BY c.mode, c.reliability_tier
        ORDER BY c.mode, c.reliability_tier
    """)
    st.dataframe(carrier_df, use_container_width=True)

# TAB 2: SHIPMENT EXPLORER & TIMELINE
with tabs[1]:
    st.subheader("Shipment Telematics & Ingestion Lag Explorer")
    
    # Filter selection
    status_filter = st.selectbox("Filter by Status", ["ALL", "ON_TIME", "DELAYED", "SEVERELY_DELAYED"], index=0)
    
    query = "SELECT shipment_id, origin_facility_id, destination_facility_id, service_level_id, final_delay_label, is_rerouted FROM shipments"
    if status_filter != "ALL":
        query += f" WHERE final_delay_label='{status_filter}'"
    query += " LIMIT 100"
    
    sample_shipments = load_query(conn, query)
    
    selected_shp_id = st.selectbox(
        "Select Shipment to Inspect",
        sample_shipments["shipment_id"].tolist(),
        index=0 if len(sample_shipments) > 0 else None,
    )

    if selected_shp_id:
        shp_data = load_query(conn, "SELECT * FROM shipments WHERE shipment_id = ?", (selected_shp_id,)).iloc[0]
        
        info_c1, info_c2, info_c3, info_c4 = st.columns(4)
        with info_c1:
            st.markdown(f"**Origin**: `{shp_data['origin_facility_id']}`")
            st.markdown(f"**Destination**: `{shp_data['destination_facility_id']}`")
        with info_c2:
            st.markdown(f"**Service Level**: `{shp_data['service_level_id']}`")
            st.markdown(f"**Route**: `{shp_data['route_id']}`")
        with info_c3:
            st.markdown(f"**Created At**: `{shp_data['created_at']}`")
            st.markdown(f"**Promised Delivery**: `{shp_data['promised_delivery_at']}`")
        with info_c4:
            st.markdown(f"**Actual Delivery**: `{shp_data['actual_delivery_at'] or 'In Transit'}`")
            badge_class = "badge-ontime" if shp_data["final_delay_label"] == "ON_TIME" else ("badge-delayed" if shp_data["final_delay_label"] == "DELAYED" else "badge-severe")
            st.markdown(f"**Outcome**: <span class='{badge_class}'>{shp_data['final_delay_label']}</span>", unsafe_allow_html=True)

        st.markdown("---")
        
        # Events & Ingestion Lag Table
        st.markdown("##### Telemetry Event Stream (`event_time` vs Database `ingestion_time`)")
        events_df = load_query(conn, """
            SELECT sequence_no, event_type, event_time, ingestion_time, 
                   ROUND((julianday(ingestion_time) - julianday(event_time)) * 24.0 * 60.0, 1) as lag_minutes,
                   source_system, is_duplicate_of
            FROM tracking_events
            WHERE shipment_id = ?
            ORDER BY sequence_no ASC
        """, (selected_shp_id,))
        st.dataframe(events_df, use_container_width=True)

        # Leg hops
        st.markdown("##### Executed Transit Legs")
        legs_df = load_query(conn, """
            SELECT leg_sequence, from_facility_id, to_facility_id, carrier_id,
                   planned_depart_at, planned_arrive_at, actual_depart_at, actual_arrive_at, leg_status
            FROM shipment_legs
            WHERE shipment_id = ?
            ORDER BY leg_sequence ASC
        """, (selected_shp_id,))
        st.dataframe(legs_df, use_container_width=True)

        # ETA Evolution Snapshots
        st.markdown("##### Leakage-Safe ETA Snapshots (Prediction Progression Over Time)")
        eta_df = load_query(conn, """
            SELECT prediction_time, method, predicted_delivery_at, n_events_used, predicted_delay_probability
            FROM eta_estimates
            WHERE shipment_id = ?
            ORDER BY prediction_time ASC
        """, (selected_shp_id,))
        st.dataframe(eta_df, use_container_width=True)

# TAB 3: FACILITY QUEUES & CONGESTION
with tabs[2]:
    st.subheader("Facility Congestion & Queue Monitoring")
    
    facilities_df = load_query(conn, "SELECT facility_id, name, type, region, capacity_per_hour FROM facilities ORDER BY facility_id")
    selected_fac_id = st.selectbox(
        "Select Facility",
        facilities_df["facility_id"].tolist(),
        format_func=lambda x: f"{x} - {facilities_df.loc[facilities_df['facility_id']==x, 'name'].values[0]} ({facilities_df.loc[facilities_df['facility_id']==x, 'type'].values[0]})"
    )

    if selected_fac_id:
        f_info = facilities_df[facilities_df["facility_id"] == selected_fac_id].iloc[0]
        f_col1, f_col2, f_col3, f_col4 = st.columns(4)
        with f_col1:
            st.metric("Facility Type", f_info["type"])
        with f_col2:
            st.metric("Region", f_info["region"])
        with f_col3:
            st.metric("Hourly Capacity", f"{f_info['capacity_per_hour']} units/hr")
        with f_col4:
            avg_wait = load_query(conn, "SELECT ROUND(AVG(avg_wait_hours), 2) as val FROM facility_queues WHERE facility_id = ?", (selected_fac_id,))["val"][0]
            st.metric("Mean Wait Time", f"{avg_wait or 0.0} hrs")

        st.markdown("---")
        st.markdown("##### Queue Length Over Time")
        queue_timeline = load_query(conn, """
            SELECT snapshot_time, queue_length, avg_wait_hours, throughput_per_hour
            FROM facility_queues
            WHERE facility_id = ?
            ORDER BY snapshot_time ASC
        """, (selected_fac_id,))
        
        if not queue_timeline.empty:
            st.line_chart(queue_timeline.set_index("snapshot_time")[["queue_length", "avg_wait_hours"]])
        else:
            st.info("No periodic queue snapshots found for this facility.")

# TAB 4: DATA QUALITY & ANOMALIES
with tabs[3]:
    st.subheader("Data Quality & Labelled Anomaly Audit")
    st.info("ℹ️ **Ground Truth Governance**: Injected anomalies are isolated to `ground_truth/` and are never exposed to feature extraction or inference pipelines.")

    gt_path = ROOT / "ground_truth" / "ground_truth.csv"
    if gt_path.exists():
        gt_df = pd.read_csv(gt_path)
        
        q1, q2, q3, q4 = st.columns(4)
        with q1:
            st.metric("Total Injected Anomalies", len(gt_df))
        with q2:
            st.metric("Timestamp Confusions", sum(gt_df["issue_type"] == "EVENT_TIME_INGESTION_CONFUSION"))
        with q3:
            st.metric("Impossible Route Orders", sum(gt_df["issue_type"] == "IMPOSSIBLE_ROUTE_ORDER"))
        with q4:
            st.metric("Future Peek ETA Leakages", sum(gt_df["issue_type"] == "ETA_USES_FUTURE_EVENT"))

        st.markdown("---")
        st.markdown("##### Injected Anomaly Audit Log")
        issue_filter = st.selectbox("Filter by Issue Type", ["ALL"] + sorted(gt_df["issue_type"].unique().tolist()))
        
        display_gt = gt_df if issue_filter == "ALL" else gt_df[gt_df["issue_type"] == issue_filter]
        st.dataframe(display_gt, use_container_width=True)
    else:
        st.warning("No ground_truth.csv file located.")

# TAB 5: OPERATIONS EXCEPTION COCKPIT
with tabs[4]:
    st.subheader("Operations Manager Exception Cockpit")
    st.markdown("Active exception queue prioritizing shipments at severe risk of SLA violation.")

    exception_df = load_query(conn, """
        SELECT s.shipment_id, s.origin_facility_id, s.destination_facility_id, s.service_level_id,
               s.final_delay_label, s.is_rerouted,
               ROUND((julianday(s.actual_delivery_at) - julianday(s.promised_delivery_at)) * 24.0, 1) as delay_hours
        FROM shipments s
        WHERE s.final_delay_label IN ('DELAYED', 'SEVERELY_DELAYED')
        ORDER BY delay_hours DESC
        LIMIT 50
    """)

    st.dataframe(exception_df, use_container_width=True)
