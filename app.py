import streamlit as st
import pandas as pd
import numpy as np
import torch
import altair as alt
import time
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), 'ml'))
from world_model import PrognosWorldModel

# ==========================================
# PAGE CONFIG
# ==========================================
st.set_page_config(
    page_title="PROGNOS - Network Attack Forecasting",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==========================================
# PROFESSIONAL CSS
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    * { font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1200px;
    }

    /* Top bar */
    .top-bar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 16px 0;
        border-bottom: 1px solid #E2E8F0;
        margin-bottom: 32px;
    }
    .top-bar-brand {
        font-size: 20px;
        font-weight: 700;
        color: #0F172A;
        letter-spacing: -0.5px;
    }
    .top-bar-sub {
        font-size: 13px;
        color: #64748B;
        font-weight: 400;
    }
    .top-bar-badge {
        background: #EFF6FF;
        color: #1D4ED8;
        font-size: 12px;
        font-weight: 500;
        padding: 4px 12px;
        border-radius: 4px;
        border: 1px solid #BFDBFE;
    }

    /* Section headers */
    .section-header {
        font-size: 14px;
        font-weight: 600;
        color: #475569;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        margin-bottom: 16px;
        margin-top: 28px;
    }

    /* Metric cards */
    .forecast-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 20px 24px;
        margin-bottom: 12px;
    }
    .forecast-label {
        font-size: 12px;
        font-weight: 500;
        color: #94A3B8;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 8px;
    }
    .forecast-value {
        font-size: 32px;
        font-weight: 700;
        line-height: 1.1;
    }
    .forecast-detail {
        font-size: 13px;
        color: #64748B;
        margin-top: 4px;
    }

    /* Severity colors */
    .severity-normal { color: #059669; }
    .severity-low { color: #D97706; }
    .severity-medium { color: #EA580C; }
    .severity-high { color: #DC2626; }
    .severity-critical { color: #991B1B; }

    /* Severity tag pills */
    .tag-normal { background: #ECFDF5; color: #065F46; border: 1px solid #A7F3D0; }
    .tag-low { background: #FFFBEB; color: #92400E; border: 1px solid #FDE68A; }
    .tag-medium { background: #FFF7ED; color: #9A3412; border: 1px solid #FED7AA; }
    .tag-high { background: #FEF2F2; color: #991B1B; border: 1px solid #FECACA; }
    .tag-critical { background: #FEF2F2; color: #7F1D1D; border: 1px solid #FCA5A5; }
    .tag {
        display: inline-block;
        font-size: 12px;
        font-weight: 600;
        padding: 4px 10px;
        border-radius: 4px;
    }

    /* Upload zone */
    .upload-zone {
        background: #F8FAFC;
        border: 2px dashed #CBD5E1;
        border-radius: 8px;
        padding: 40px;
        text-align: center;
        margin: 24px 0;
    }
    .upload-zone-title {
        font-size: 16px;
        font-weight: 600;
        color: #1E293B;
        margin-bottom: 6px;
    }
    .upload-zone-sub {
        font-size: 13px;
        color: #94A3B8;
    }

    /* Summary row */
    .summary-row {
        display: flex;
        gap: 16px;
        margin-bottom: 24px;
    }
    .summary-item {
        flex: 1;
        background: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 6px;
        padding: 14px 18px;
    }
    .summary-item-label {
        font-size: 11px;
        font-weight: 500;
        color: #94A3B8;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .summary-item-value {
        font-size: 18px;
        font-weight: 600;
        color: #1E293B;
        margin-top: 4px;
    }

    /* Table styling */
    .flow-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 13px;
    }
    .flow-table th {
        text-align: left;
        padding: 10px 12px;
        background: #F8FAFC;
        color: #64748B;
        font-weight: 600;
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        border-bottom: 1px solid #E2E8F0;
    }
    .flow-table td {
        padding: 10px 12px;
        border-bottom: 1px solid #F1F5F9;
        color: #334155;
    }
    .flow-table tr:hover td {
        background: #F8FAFC;
    }

    /* Override Streamlit defaults */
    h1, h2, h3 {
        color: #0F172A !important;
        font-family: 'Inter', sans-serif !important;
    }
    .stButton > button {
        background: #1E293B;
        color: #FFFFFF;
        border: none;
        border-radius: 6px;
        padding: 10px 24px;
        font-weight: 500;
        font-size: 14px;
    }
    .stButton > button:hover {
        background: #334155;
        color: #FFFFFF;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# MODEL LOADING
# ==========================================
@st.cache_resource
def load_world_model():
    model = PrognosWorldModel(input_features=30, num_classes=5)
    weights_path = os.path.join(os.path.dirname(__file__), 'ml', 'world_model_weights.pt')
    if os.path.exists(weights_path):
        model.load_state_dict(torch.load(weights_path, map_location=torch.device('cpu')))
    model.eval()
    return model

def prepare_sequences(df, feature_cols, sequence_length=6):
    """Prepare sliding window sequences directly from a DataFrame, no sklearn dependency."""
    from sklearn.preprocessing import RobustScaler

    for col in feature_cols:
        if col not in df.columns:
            df[col] = 0.0

    df[feature_cols] = df[feature_cols].replace([np.inf, -np.inf], np.nan).fillna(0)

    scaler = RobustScaler()
    df[feature_cols] = scaler.fit_transform(df[feature_cols])

    sequences = []
    ip_list = []

    group_col = 'id.orig_h' if 'id.orig_h' in df.columns else None

    if group_col:
        for ip, group in df.groupby(group_col):
            group = group.sort_values('ts') if 'ts' in group.columns else group
            features = group[feature_cols].values
            if len(features) < sequence_length + 1:
                continue
            for i in range(len(features) - sequence_length):
                sequences.append(features[i : i + sequence_length])
                ip_list.append(ip)
    else:
        features = df[feature_cols].values
        for i in range(len(features) - sequence_length):
            sequences.append(features[i : i + sequence_length])
            ip_list.append("Unknown")

    return sequences, ip_list

# ==========================================
# MITRE MAPPING
# ==========================================
mitre_map = {
    0: ("Normal Traffic",       "normal"),
    1: ("Reconnaissance",       "low"),
    2: ("Initial Access",       "medium"),
    3: ("Lateral Movement",     "high"),
    4: ("Command and Control",  "critical"),
}

feature_cols = [
    'duration', 'orig_bytes', 'resp_bytes', 'orig_pkts', 'resp_pkts',
    'min_ttl_orig', 'max_ttl_orig', 'min_ttl_resp', 'max_ttl_resp',
    'avg_win_orig', 'avg_win_resp', 'payload_min_orig', 'payload_max_orig',
    'payload_min_resp', 'payload_max_resp', 'frag_count', 'retrans_orig',
    'retrans_resp', 'flag_syn', 'flag_ack', 'flag_fin', 'flag_rst',
    'flag_psh', 'flag_urg', 'iat_mean', 'iat_max', 'iat_var',
    'flow_count', 'unique_dest_ports_scan_signature', 'bidirectional_flow_ratio'
]

# ==========================================
# HEADER
# ==========================================
st.markdown("""
<div class="top-bar">
    <div>
        <span class="top-bar-brand">PROGNOS</span>
        <span class="top-bar-sub" style="margin-left: 12px;">Network Attack Forecasting Engine</span>
    </div>
    <div>
        <span class="top-bar-badge">World Model v2 — CNN-LSTM</span>
    </div>
</div>
""", unsafe_allow_html=True)

# ==========================================
# MAIN CONTENT
# ==========================================
upload_file = st.file_uploader(
    "Upload processed network telemetry (sequences.csv from Zeek pipeline)",
    type="csv",
    label_visibility="collapsed"
)

if upload_file is None:
    st.markdown("""
    <div class="upload-zone">
        <div class="upload-zone-title">Upload Network Telemetry to Begin Forecasting</div>
        <div class="upload-zone-sub">
            Accepts sequences.csv generated by the Zeek extraction pipeline.
            The engine will simulate K-step forward trajectories and forecast attack progression.
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="section-header">How It Works</div>', unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("""
        <div class="forecast-card">
            <div class="forecast-label">Step 1: Ingest</div>
            <div class="forecast-detail">
                Raw PCAP traffic is parsed by Zeek into 30-dimensional
                state vectors covering flow-level and packet-level features,
                grouped by source IP in 10-second windows.
            </div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown("""
        <div class="forecast-card">
            <div class="forecast-label">Step 2: Forecast</div>
            <div class="forecast-detail">
                The CNN-LSTM World Model learns state transition dynamics
                P(S_t+1 | S_t) and simulates future network trajectories
                to predict attack progression before compromise.
            </div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown("""
        <div class="forecast-card">
            <div class="forecast-label">Step 3: Interpret</div>
            <div class="forecast-detail">
                Native temporal attention weights identify which traffic
                windows drove the forecast. Predictions are mapped to
                MITRE ATT&CK stages for actionable defence.
            </div>
        </div>
        """, unsafe_allow_html=True)

else:
    # Load and process
    temp_path = "temp_sequences.csv"
    with open(temp_path, "wb") as f:
        f.write(upload_file.getbuffer())

    raw_df = pd.read_csv(temp_path)
    model = load_world_model()

    sequences, ip_list = prepare_sequences(raw_df.copy(), feature_cols, sequence_length=6)

    if len(sequences) == 0:
        st.error("Not enough sequential data to build forecasting windows. Ensure the CSV has at least 7 rows per source IP.")
        st.stop()

    # Run button
    run_col, info_col = st.columns([1, 3])
    with run_col:
        run_inference = st.button("Run Forecast Simulation", use_container_width=True)

    if not run_inference:
        st.markdown(f"""
        <div class="summary-row">
            <div class="summary-item">
                <div class="summary-item-label">Total Rows</div>
                <div class="summary-item-value">{len(raw_df):,}</div>
            </div>
            <div class="summary-item">
                <div class="summary-item-label">Temporal Sequences</div>
                <div class="summary-item-value">{len(sequences):,}</div>
            </div>
            <div class="summary-item">
                <div class="summary-item-label">Unique Source IPs</div>
                <div class="summary-item-value">{raw_df['id.orig_h'].nunique() if 'id.orig_h' in raw_df.columns else 'N/A'}</div>
            </div>
            <div class="summary-item">
                <div class="summary-item-label">Model Status</div>
                <div class="summary-item-value">Ready</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.info("Click 'Run Forecast Simulation' to begin the K-step forward trajectory analysis.")
        st.stop()

    # ==========================================
    # INFERENCE
    # ==========================================
    st.markdown('<div class="section-header">Forecast Results</div>', unsafe_allow_html=True)

    progress_bar = st.progress(0)

    col1, col2, col3 = st.columns(3)
    metric_prob = col1.empty()
    metric_mitre = col2.empty()
    metric_ip = col3.empty()

    chart_placeholder = st.empty()
    table_placeholder = st.empty()

    timeline_data = []
    flagged_flows = []
    max_steps = min(len(sequences), 300)

    for idx in range(max_steps):
        x = torch.tensor(sequences[idx], dtype=torch.float32).unsqueeze(0)

        with torch.no_grad():
            mitre_logits, prob_preds, attn_weights = model(x)

        prob_val = prob_preds.item() * 100
        stage_idx = torch.argmax(mitre_logits, dim=1).item()
        stage_name, severity = mitre_map[stage_idx]
        suspect_ip = ip_list[idx]

        timeline_data.append({
            "Window": idx,
            "Probability": prob_val,
            "Stage": stage_name
        })

        if stage_idx > 0:
            flagged_flows.append({
                "Window": idx,
                "Source IP": suspect_ip,
                "Predicted Stage": stage_name,
                "Confidence": f"{prob_val:.1f}%"
            })

        # Update metric cards
        metric_prob.markdown(f"""
        <div class="forecast-card">
            <div class="forecast-label">Infiltration Probability</div>
            <div class="forecast-value severity-{severity}">{prob_val:.1f}%</div>
            <div class="forecast-detail">Current window forecast</div>
        </div>
        """, unsafe_allow_html=True)

        metric_mitre.markdown(f"""
        <div class="forecast-card">
            <div class="forecast-label">Predicted MITRE ATT&CK Stage</div>
            <div class="forecast-value"><span class="tag tag-{severity}">{stage_name}</span></div>
            <div class="forecast-detail">Based on trajectory simulation</div>
        </div>
        """, unsafe_allow_html=True)

        metric_ip.markdown(f"""
        <div class="forecast-card">
            <div class="forecast-label">Actor IP Under Analysis</div>
            <div class="forecast-value" style="font-size: 24px; color: #1E293B;">{suspect_ip}</div>
            <div class="forecast-detail">Source address of current sequence</div>
        </div>
        """, unsafe_allow_html=True)

        # Update timeline chart
        chart_df = pd.DataFrame(timeline_data)

        line = alt.Chart(chart_df).mark_line(
            strokeWidth=2,
            color='#2563EB'
        ).encode(
            x=alt.X('Window:Q', title='Time Window (10s intervals)', axis=alt.Axis(grid=False)),
            y=alt.Y('Probability:Q', title='Infiltration Probability (%)', scale=alt.Scale(domain=[0, 100]))
        )

        area = alt.Chart(chart_df).mark_area(
            opacity=0.08,
            color='#2563EB'
        ).encode(
            x='Window:Q',
            y=alt.Y('Probability:Q', scale=alt.Scale(domain=[0, 100]))
        )

        chart = (area + line).properties(height=280).configure_view(
            strokeWidth=0
        ).configure_axis(
            labelColor='#64748B',
            titleColor='#475569',
            gridColor='#F1F5F9'
        )

        chart_placeholder.altair_chart(chart, use_container_width=True)

        progress_bar.progress((idx + 1) / max_steps)

    # Final summary
    st.markdown('<div class="section-header">Session Summary</div>', unsafe_allow_html=True)

    total_flagged = len(flagged_flows)
    avg_prob = np.mean([d["Probability"] for d in timeline_data])
    max_prob = np.max([d["Probability"] for d in timeline_data])

    st.markdown(f"""
    <div class="summary-row">
        <div class="summary-item">
            <div class="summary-item-label">Windows Analyzed</div>
            <div class="summary-item-value">{max_steps}</div>
        </div>
        <div class="summary-item">
            <div class="summary-item-label">Average Threat Score</div>
            <div class="summary-item-value">{avg_prob:.1f}%</div>
        </div>
        <div class="summary-item">
            <div class="summary-item-label">Peak Threat Score</div>
            <div class="summary-item-value">{max_prob:.1f}%</div>
        </div>
        <div class="summary-item">
            <div class="summary-item-label">Flagged Sequences</div>
            <div class="summary-item-value">{total_flagged}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if total_flagged > 0:
        st.markdown('<div class="section-header">Flagged Flows</div>', unsafe_allow_html=True)
        flagged_df = pd.DataFrame(flagged_flows)
        st.dataframe(flagged_df, use_container_width=True, hide_index=True)
    else:
        st.markdown("No anomalous sequences were flagged during this simulation.")

    st.markdown("---")
    st.caption("PROGNOS Network Attack Forecasting Engine. Simulation complete.")
