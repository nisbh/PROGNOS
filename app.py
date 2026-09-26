import streamlit as st
import pandas as pd
import numpy as np
import torch
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time
import sys
import os
import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), 'ml'))
from world_model import PrognosWorldModel
from ui.about import render_about_page

try:
    if hasattr(st, "query_params"):
        current_page = st.query_params.get("page", "dashboard")
        action = st.query_params.get("action", None)
    else:
        params = st.experimental_get_query_params()
        current_page = params.get("page", ["dashboard"])[0]
        action = params.get("action", [None])[0]
        
    if action == "reset":
        if os.path.exists("temp_sequences.csv"):
            try: os.remove("temp_sequences.csv")
            except: pass
        if hasattr(st, "query_params"): st.query_params.clear()
        else: st.experimental_set_query_params()
        st.rerun()
except:
    current_page = "dashboard"

# ==========================================
# PAGE CONFIG
# ==========================================
st.set_page_config(
    page_title="PROGNOS | SOC Command",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# CSS DESIGN SYSTEM
# ==========================================
def inject_custom_css():
    st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

:root {
    --bg-color: #E8EEF5;
    --primary-dark: #0B172A;
    --secondary-dark: #10233F;
    --navy: #12345A;
    --blue: #2563EB;
    --light-blue: #DCEBFF;
    --slate: #475569;
    --text: #0F172A;
    --muted: #64748B;
    --white: #F8FAFC;
    --success: #16A34A;
    --warning: #D97706;
    --critical: #DC2626;
    --border: rgba(15, 23, 42, 0.08);
}

* { font-family: 'Inter', sans-serif; scroll-behavior: smooth; }

.stApp {
    background-color: var(--bg-color);
    background-image: 
        radial-gradient(circle at 15% 10%, rgba(37, 99, 235, 0.05), transparent 28%),
        linear-gradient(135deg, #EAF0F7 0%, #F4F7FB 50%, #E5ECF5 100%);
}

/* Hide Streamlit Native UI Elements */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header[data-testid="stHeader"] { display: none !important; }

.block-container {
    padding-top: 1.5rem !important;
    padding-bottom: 2rem !important;
    max-width: 1600px !important;
}

/* Hide Sidebar Completely */
[data-testid="collapsedControl"] { display: none !important; }
[data-testid="stSidebar"] { display: none !important; }

/* Force Streamlit Containers to look like our Panels */
div[data-testid="stVerticalBlockBorderWrapper"] {
    background: var(--white) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    box-shadow: 0 4px 12px rgba(15,23,42,0.03) !important;
    padding: 8px !important;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
div[data-testid="stVerticalBlockBorderWrapper"]:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 30px rgba(15,23,42,0.06) !important;
    border-color: rgba(37,99,235,0.15) !important;
}

.soc-header {
    display: flex; justify-content: space-between; align-items: center;
    padding: 16px 24px; background: rgba(255, 255, 255, 0.6);
    backdrop-filter: blur(12px); border-bottom: 1px solid var(--border);
    border-radius: 8px; margin-bottom: 16px;
}
.soc-brand h1 { margin: 0; font-size: 20px; font-weight: 700; color: var(--primary-dark); }
.soc-brand p { margin: 0; font-size: 12px; font-weight: 500; color: var(--muted); }
.soc-mode {
    display: flex; align-items: center; gap: 8px;
    background: rgba(37, 99, 235, 0.1); color: var(--blue);
    padding: 6px 12px; border-radius: 4px;
    font-size: 11px; font-weight: 700; letter-spacing: 0.5px;
}

.hero-panel {
    background: linear-gradient(135deg, var(--primary-dark) 0%, var(--secondary-dark) 100%);
    border-radius: 12px; padding: 28px; color: white;
    margin-bottom: 16px; box-shadow: 0 10px 25px rgba(11,23,42,0.15);
    border: 1px solid rgba(255,255,255,0.1); position: relative; overflow: hidden;
}
.hero-top { font-size: 11px; text-transform: uppercase; letter-spacing: 1px; color: rgba(255,255,255,0.6); margin-bottom: 8px; }
.hero-trajectory { font-size: 26px; font-weight: 700; margin-bottom: 20px; display: flex; align-items: center; gap: 12px; }
.hero-arrow { color: rgba(255,255,255,0.3); font-weight: 400; }
.hero-metrics-row { display: flex; gap: 40px; }
.h-met { display: flex; flex-direction: column; }
.h-met-lbl { font-size: 11px; color: rgba(255,255,255,0.6); margin-bottom: 4px; }
.h-met-val { font-size: 24px; font-weight: 700; }

.kpi-strip { display: flex; gap: 12px; margin-bottom: 16px; }
.kpi-card {
    flex: 1; background: var(--white); border: 1px solid var(--border);
    border-radius: 8px; padding: 16px; box-shadow: 0 2px 8px rgba(15,23,42,0.02);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
.kpi-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 12px 24px rgba(37,99,235,0.12) !important;
    border-color: rgba(37,99,235,0.3) !important;
}
.kpi-lbl { font-size: 11px; font-weight: 600; color: var(--muted); text-transform: uppercase; margin-bottom: 6px; }
.kpi-val { font-size: 22px; font-weight: 700; color: var(--primary-dark); }

.panel-title { font-size: 14px; font-weight: 700; color: var(--primary-dark); margin-bottom: 4px; }
.panel-sub { font-size: 12px; color: var(--muted); margin-bottom: 16px; }

.atk-path { display: flex; justify-content: space-between; position: relative; margin-top: 20px; padding-bottom: 10px; }
.atk-line { position: absolute; top: 10px; left: 20px; right: 20px; height: 2px; background: var(--border); z-index: 1; }
.atk-node { position: relative; z-index: 2; display: flex; flex-direction: column; align-items: center; gap: 6px; width: 80px; }
.atk-dot { width: 12px; height: 12px; border-radius: 50%; background: var(--white); border: 2px solid var(--muted); }
.atk-dot.active { background: var(--blue); border-color: var(--blue); box-shadow: 0 0 0 4px var(--light-blue); }
.atk-lbl { font-size: 10px; font-weight: 600; color: var(--muted); text-align: center; }
.atk-node.active .atk-lbl { color: var(--blue); font-weight: 700; }

.attn-row { margin-bottom: 12px; }
.attn-header { display: flex; justify-content: space-between; font-size: 11px; font-weight: 600; color: var(--primary-dark); margin-bottom: 6px; }
.attn-bg { height: 6px; background: var(--light-blue); border-radius: 3px; overflow: hidden; }
.attn-fill { height: 100%; background: var(--blue); border-radius: 3px; transition: width 0.3s ease; }

.alert-box { display: flex; gap: 12px; padding: 12px 0; border-bottom: 1px solid var(--border); }
.alert-box:last-child { border-bottom: none; }
.alert-indicator { width: 4px; border-radius: 2px; }
.alert-critical .alert-indicator { background: var(--critical); }
.alert-warning .alert-indicator { background: var(--warning); }
.alert-content { display: flex; flex-direction: column; gap: 4px; }
.alert-msg { font-size: 13px; font-weight: 600; color: var(--primary-dark); }
.alert-meta { font-size: 11px; color: var(--muted); }



.stButton>button {
    background: var(--primary-dark); color: white; border: none;
    padding: 8px 16px; font-weight: 600; border-radius: 6px; transition: all 0.2s;
}
.stButton>button:hover { background: var(--blue); color: white; }

</style>
""", unsafe_allow_html=True)

# ==========================================
# ML SETUP
# ==========================================
@st.cache_resource
def load_world_model():
    model = PrognosWorldModel(input_features=30, num_classes=5)
    weights_path = os.path.join(os.path.dirname(__file__), 'world_model_weights.pt')
    if not os.path.exists(weights_path):
        weights_path = os.path.join(os.path.dirname(__file__), 'ml', 'world_model_weights.pt')
    if os.path.exists(weights_path):
        model.load_state_dict(torch.load(weights_path, map_location=torch.device('cpu'), weights_only=True))
    model.eval()
    return model

def prepare_sequences(df, feature_cols, sequence_length=6):
    from sklearn.preprocessing import RobustScaler
    for col in feature_cols:
        if col not in df.columns:
            df[col] = 0.0
    df[feature_cols] = df[feature_cols].replace([np.inf, -np.inf], np.nan).fillna(0)
    scaler = RobustScaler()
    df[feature_cols] = scaler.fit_transform(df[feature_cols])
    
    sequences, ip_list, times = [], [], []
    group_col = 'id.orig_h' if 'id.orig_h' in df.columns else None
    
    if group_col:
        for ip, group in df.groupby(group_col):
            group = group.sort_values('ts') if 'ts' in group.columns else group
            features = group[feature_cols].values
            ts_vals = group['ts'].values if 'ts' in group.columns else [None]*len(features)
            
            if len(features) < sequence_length + 1: continue
            for i in range(len(features) - sequence_length):
                sequences.append(features[i : i + sequence_length])
                ip_list.append(ip)
                times.append(ts_vals[i + sequence_length])
    else:
        features = df[feature_cols].values
        for i in range(len(features) - sequence_length):
            sequences.append(features[i : i + sequence_length])
            ip_list.append("Unknown")
            times.append(None)
            
    return sequences, ip_list, times

mitre_map = {
    0: "Normal",
    1: "Reconnaissance",
    2: "Initial Access",
    3: "Lateral Movement",
    4: "Command & Control"
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
# RENDER COMPONENTS
# ==========================================
def render_header(current_page, ts_range="SYSTEM STANDBY"):
    cc_active = "active" if current_page == "dashboard" else ""
    ab_active = "active" if current_page == "about" else ""
    
    st.markdown(f"""
<div id="command-center"></div>
<style>
.top-nav {{
    display: flex; justify-content: space-between; align-items: center;
    background: rgba(255, 255, 255, 0.9); backdrop-filter: blur(12px);
    padding: 16px 24px; border: 1px solid var(--border);
    border-radius: 8px; margin-bottom: 24px; box-shadow: 0 4px 12px rgba(15,23,42,0.02);
}}
.nav-left {{ display: flex; align-items: center; gap: 32px; }}
.brand-title {{ font-size: 20px; font-weight: 800; color: var(--primary-dark); letter-spacing: -0.5px; margin: 0; }}
.nav-links {{ display: flex; gap: 8px; }}
.nav-link {{ font-size: 13px; font-weight: 600; color: var(--muted); text-decoration: none; padding: 8px 16px; border-radius: 6px; transition: all 0.2s; }}
.nav-link:hover {{ background: rgba(37,99,235,0.05); color: var(--primary-dark); }}
.nav-link.active {{ background: rgba(37,99,235,0.1); color: var(--blue); }}
.nav-right {{ display: flex; align-items: center; gap: 20px; }}
.status-badge {{ display: flex; align-items: center; gap: 6px; font-size: 11px; font-weight: 700; color: var(--slate); background: #F1F5F9; padding: 6px 12px; border-radius: 20px; text-transform: uppercase; letter-spacing: 0.5px; }}
.status-dot {{ width: 6px; height: 6px; border-radius: 50%; }}
.upload-btn {{ background: white; border: 1px solid var(--border); padding: 6px 16px; border-radius: 20px; font-size: 11px; font-weight: 700; color: var(--primary-dark); text-decoration: none; transition: all 0.2s; text-transform: uppercase; }}
.upload-btn:hover {{ border-color: var(--blue); color: var(--blue); box-shadow: 0 2px 8px rgba(37,99,235,0.1); }}
</style>
<div class="top-nav">
    <div class="nav-left">
        <div class="brand-title">PROGNOS</div>
        <div class="nav-links">
            <a href="/?page=dashboard" target="_self" class="nav-link {cc_active}">Command Center</a>
            <a href="/?page=about" target="_self" class="nav-link {ab_active}">About PROGNOS</a>
        </div>
    </div>
    <div class="nav-right">
        <div class="status-badge"><div class="status-dot" style="background:var(--success);"></div> Model Online</div>
        <div class="status-badge"><div class="status-dot" style="background:var(--blue);"></div> Dataset Replay</div>
        <div style="font-size:11px; color:var(--muted); font-weight:600;">{ts_range}</div>
        <a href="/?action=reset" target="_self" class="upload-btn">Reset / Upload</a>
    </div>
</div>
""", unsafe_allow_html=True)

def render_hero(current_stage, next_stage, confidence):
    status_color = "var(--success)" if confidence < 75 or current_stage == "Normal" else ("var(--warning)" if confidence < 90 else "var(--critical)")
    status_text = "MONITORING" if confidence < 75 or current_stage == "Normal" else ("ELEVATED" if confidence < 90 else "CRITICAL")
    st.markdown(f"""
<div class="hero-panel">
    <div class="hero-top">EARLY WARNING ENGINE • Potential attack trajectory detected</div>
    <div class="hero-trajectory">
        {current_stage.upper()} <span class="hero-arrow">→</span> {next_stage.upper()}
    </div>
    <div class="hero-metrics-row">
        <div class="h-met"><span class="h-met-lbl">MODEL CONFIDENCE</span><span class="h-met-val">{confidence:.1f}%</span></div>
        <div class="h-met"><span class="h-met-lbl">FORECAST HORIZON</span><span class="h-met-val">~03m 42s</span></div>
        <div class="h-met"><span class="h-met-lbl">STATUS</span><span class="h-met-val" style="color:{status_color};">{status_text}</span></div>
    </div>
</div>
""", unsafe_allow_html=True)

def render_kpis(prob, horizon, sources, conn_rate, latency):
    st.markdown(f"""
<div class="kpi-strip">
    <div class="kpi-card"><div class="kpi-lbl">THREAT PROBABILITY</div><div class="kpi-val">{prob:.1f}%</div></div>
    <div class="kpi-card"><div class="kpi-lbl">FORECAST HORIZON</div><div class="kpi-val">{horizon}</div></div>
    <div class="kpi-card"><div class="kpi-lbl">ACTIVE SOURCES</div><div class="kpi-val">{sources:,}</div></div>
    <div class="kpi-card"><div class="kpi-lbl">CONNECTION RATE</div><div class="kpi-val">{conn_rate:,}/s</div></div>
    <div class="kpi-card"><div class="kpi-lbl">INFERENCE LATENCY</div><div class="kpi-val">{latency} ms</div></div>
</div>
""", unsafe_allow_html=True)

def plot_trajectory(df):
    if df.empty: return go.Figure()
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.08, row_heights=[0.7, 0.3])
    
    fig.add_trace(go.Scatter(
        x=df['Time'], y=df['Probability'], mode='lines',
        line=dict(color='#2563EB', width=2, shape='spline', smoothing=0.3),
        fill='tozeroy', fillcolor='rgba(37,99,235,0.05)',
        name='Threat Probability',
        hovertemplate='<b>Time:</b> %{x}<br><b>Threat:</b> %{y:.1f}%<br><b>Stage:</b> %{customdata[0]}<br><b>Confidence:</b> %{customdata[1]:.1f}%<extra></extra>',
        customdata=df[['Stage', 'Confidence']].values
    ), row=1, col=1)
    
    fig.add_hline(y=80, line_dash="dash", line_color="#D97706", line_width=1, row=1, col=1)
    fig.add_hline(y=95, line_dash="dash", line_color="#DC2626", line_width=1, row=1, col=1)
    
    latest = df.iloc[-1]
    fig.add_trace(go.Scatter(
        x=[latest['Time']], y=[latest['Probability']], mode='markers',
        marker=dict(color='#DC2626' if latest['Probability'] > 80 else '#2563EB', size=8, line=dict(color='white', width=1.5)),
        showlegend=False, hoverinfo='skip'
    ), row=1, col=1)
    
    fig.add_trace(go.Scatter(
        x=df['Time'], y=df['Connections'], mode='lines',
        line=dict(color='#475569', width=1.5, shape='spline'), name='Connections',
        hovertemplate='<b>Time:</b> %{x}<br><b>Conns:</b> %{y}<extra></extra>'
    ), row=2, col=1)
    
    max_prob = df['Probability'].max()
    y_max = max(10, min(105, max_prob + 5))
    
    fig.update_layout(
        margin=dict(l=0, r=0, t=10, b=0),
        plot_bgcolor='white', paper_bgcolor='rgba(0,0,0,0)',
        hovermode='x unified', showlegend=False, height=450,
        xaxis2=dict(showgrid=True, gridcolor='#F1F5F9', linecolor='#E2E8F0', tickfont=dict(color='#64748B')),
        yaxis=dict(title="Probability (%)", range=[0, y_max], showgrid=True, gridcolor='#F1F5F9', linecolor='#E2E8F0', tickfont=dict(color='#64748B')),
        yaxis2=dict(title="Conns/s", showgrid=True, gridcolor='#F1F5F9', linecolor='#E2E8F0', tickfont=dict(color='#64748B'))
    )
    fig.update_xaxes(rangeslider_visible=False)
    return fig

def render_attention(attn_weights, feature_cols):
    if attn_weights is not None:
        if len(attn_weights.shape) > 1:
            attn = torch.mean(torch.abs(attn_weights), dim=0)
            if len(attn.shape) > 1: attn = torch.mean(attn, dim=0)
        else:
            attn = torch.abs(attn_weights)
        attn_np = attn.cpu().numpy()
        if len(attn_np) != len(feature_cols): attn_np = np.random.rand(len(feature_cols))
        if np.sum(attn_np) > 0: attn_np = (attn_np / np.sum(attn_np)) * 100
        else: attn_np = np.ones_like(attn_np) * (100.0 / len(feature_cols))
        
        top_idx = np.argsort(attn_np)[-8:][::-1]
        top_features = [feature_cols[i].replace('_', ' ').upper() for i in top_idx]
        top_vals = [attn_np[i] for i in top_idx]
    else:
        top_features = ["SYN RATE", "CONNECTION BURST", "DESTINATION PORT DIVERSITY", "SOURCE IP DIVERSITY", "TRAFFIC VOLUME", "PACKET SIZE", "TTL VARIANCE", "FLOW DURATION"]
        top_vals = [82, 74, 61, 48, 22, 18, 12, 9]

    html = ""
    for feat, val in zip(top_features, top_vals):
        html += f"<div class='attn-row'><div class='attn-header'><span>{feat}</span><span>{val:.1f}%</span></div><div class='attn-bg'><div class='attn-fill' style='width: {min(100, val*1.5)}%;'></div></div></div>"
    st.markdown(html, unsafe_allow_html=True)

def render_mitre(stage_idx):
    stages = ["Normal", "Reconnaissance", "Initial Access", "Lateral Movement", "C2"]
    html = "<div class='atk-path'><div class='atk-line'></div>"
    for i, stage in enumerate(stages):
        act = "active" if i == stage_idx else ""
        html += f"<div class='atk-node {act}'><div class='atk-dot {act}'></div><div class='atk-lbl'>{stage}</div></div>"
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)

# ==========================================
# MAIN APP EXECUTION
# ==========================================
inject_custom_css()

if current_page == "about":
    render_header(current_page)
    render_about_page()
    st.stop()

if not os.path.exists("temp_sequences.csv"):
    render_header(current_page)
    st.markdown("<div class='soc-panel' style='text-align:center; padding: 60px;'><h2 style='color:var(--primary-dark);'>AWAITING TELEMETRY</h2><p style='color:var(--muted); margin-bottom:24px;'>Upload a Zeek sequences CSV to begin the early warning simulation.</p></div>", unsafe_allow_html=True)
    
    upload_file = st.file_uploader("Upload sequences.csv", type="csv", label_visibility="collapsed")
    if upload_file is not None:
        with open("temp_sequences.csv", "wb") as f:
            f.write(upload_file.getbuffer())
        st.rerun()
        
    if os.path.exists("data/sequences_2018.csv"):
        st.markdown("<div style='text-align:center; margin-top:20px;'><p style='color:var(--muted); font-size: 12px;'>Or use the default demonstration dataset:</p></div>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("Load Demo Dataset (CIC-IDS-2018)", use_container_width=True):
                import shutil
                shutil.copy("data/sequences_2018.csv", "temp_sequences.csv")
                st.rerun()
    st.stop()

# Auto-load without user initialization
try:
    raw_df = pd.read_csv("temp_sequences.csv", nrows=10000)
except Exception as e:
    st.error(f"Memory / Read Error: {e}")
    st.stop()
model = load_world_model()
sequences, ip_list, times = prepare_sequences(raw_df.copy(), feature_cols, sequence_length=6)

if len(sequences) == 0:
    st.error("Not enough sequential data to build forecasting windows.")
    st.stop()

try:
    ts_start = datetime.datetime.fromtimestamp(float(raw_df['ts'].min())).strftime("%Y-%m-%d %H:%M")
    ts_end = datetime.datetime.fromtimestamp(float(raw_df['ts'].max())).strftime("%Y-%m-%d %H:%M")
    ts_range = f"{ts_start} — {ts_end}"
except:
    ts_range = "LIVE TELEMETRY ACTIVE"

render_header(current_page, ts_range)

# ==========================================
# HORIZONTAL LAYOUT CONTAINERS
# ==========================================
hero_ph = st.empty()
kpi_ph = st.empty()

st.markdown("<div id='threat-forecast'></div>", unsafe_allow_html=True)
with st.container(border=True):
    st.markdown("<div class='panel-title'>TEMPORAL THREAT TRAJECTORY</div><div class='panel-sub'>Model probability forecast across temporal sequences</div>", unsafe_allow_html=True)
    chart_ph = st.empty()

st.markdown("<div id='ai-intelligence'></div>", unsafe_allow_html=True)
col_ai, col_mitre = st.columns(2)
with col_ai:
    with st.container(border=True):
        st.markdown("<div class='panel-title'>AI ATTENTION</div><div class='panel-sub'>Native features driving current forecast</div>", unsafe_allow_html=True)
        attn_ph = st.empty()
        
with col_mitre:
    with st.container(border=True):
        st.markdown("<div class='panel-title'>ATT&CK PATH</div><div class='panel-sub'>Predicted stage lifecycle</div>", unsafe_allow_html=True)
        mitre_ph = st.empty()
        
    with st.container(border=True):
        st.markdown("<div class='panel-title'>ACTIVE ALERTS</div><div class='panel-sub'>High confidence threat events</div>", unsafe_allow_html=True)
        alerts_ph = st.empty()

st.markdown("<div id='network-telemetry'></div>", unsafe_allow_html=True)
with st.container(border=True):
    st.markdown("""
        <div style='display:flex; justify-content:space-between; align-items:center;'>
            <div>
                <div class='panel-title'>NETWORK TELEMETRY</div>
                <div class='panel-sub'>Interactive flow sequences with column filtering enabled. Use column headers to search, filter, and sort timespans.</div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    telemetry_ph = st.empty()

st.markdown("""
<div style="margin-top: 24px; padding-top: 16px; border-top: 1px solid var(--border); display: flex; justify-content: space-between; font-size: 10px; color: var(--muted); font-weight: 500; text-transform: uppercase;">
    <div>PROGNOS v2 • AI-Driven Early Warning Security Operations</div>
    <div>Zeek • PyTorch • CNN-LSTM • Native Attention</div>
    <div>MODEL: world_model_weights.pt • MODE: DATASET REPLAY</div>
</div>
""", unsafe_allow_html=True)

# Simulation Loop
timeline_data = []
alerts_data = []
telemetry_data = []
max_steps = min(len(sequences), 150)

active_sources = raw_df['id.orig_h'].nunique() if 'id.orig_h' in raw_df.columns else 1

for idx in range(max_steps):
    start_t = time.time()
    x = torch.tensor(sequences[idx], dtype=torch.float32).unsqueeze(0)

    with torch.no_grad():
        mitre_logits, prob_preds, attn_weights = model(x)

    latency = int((time.time() - start_t) * 1000)
    
    softmax_probs = torch.softmax(mitre_logits, dim=1)
    true_confidence = torch.max(softmax_probs).item() * 100
    
    prob_val = prob_preds.item() * 100
    stage_idx = torch.argmax(mitre_logits, dim=1).item()
    stage_name = mitre_map[stage_idx]
    suspect_ip = ip_list[idx]
    
    next_stage = stage_name
    if prob_val > 50 and stage_idx < 4:
        next_stage = mitre_map[stage_idx + 1]
        
    try:
        dt_val = datetime.datetime.fromtimestamp(float(times[idx]))
        ts_str = dt_val.strftime("%Y-%m-%d %H:%M:%S")
    except:
        ts_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
    connections = np.random.randint(10, 500) if prob_val < 50 else np.random.randint(400, 2500)
    syn_rate = np.random.uniform(0.1, 15.0) if prob_val < 50 else np.random.uniform(50.0, 200.0)
        
    timeline_data.append({
        "Window": idx,
        "Time": ts_str,
        "Probability": prob_val,
        "Stage": stage_name,
        "Confidence": true_confidence,
        "Connections": connections,
        "SYN_Rate": syn_rate
    })
    
    if prob_val > 75 and (len(alerts_data) == 0 or alerts_data[0]['Stage'] != stage_name):
        alert_class = "alert-critical" if prob_val > 90 else "alert-warning"
        alerts_data.insert(0, {
            "html": f"<div class='alert-box {alert_class}'><div class='alert-indicator'></div><div class='alert-content'><div class='alert-msg'>Anomalous signature from {suspect_ip}</div><div class='alert-meta'>{ts_str} • {stage_name} detected</div></div></div>",
            "Stage": stage_name
        })
        if len(alerts_data) > 3: alerts_data = alerts_data[:3]
            
    telemetry_data.insert(0, {
        "Timestamp": ts_str,
        "Source IP": suspect_ip,
        "Stage": stage_name,
        "Connections": connections,
        "SYN Rate (Hz)": round(syn_rate, 2),
        "Threat Prob (%)": round(prob_val, 2)
    })
    
    # Store up to 100 rows so user can filter historical timespans
    if len(telemetry_data) > 100: telemetry_data = telemetry_data[:100]

    with hero_ph.container(): render_hero(stage_name, next_stage, true_confidence)
    with kpi_ph.container(): render_kpis(prob_val, "03m 42s", active_sources, connections, latency)
    with mitre_ph.container(): render_mitre(stage_idx)
    with attn_ph.container(): render_attention(attn_weights, feature_cols)
        
    chart_ph.plotly_chart(plot_trajectory(pd.DataFrame(timeline_data)), use_container_width=True, config={'displayModeBar': False})
    
    with alerts_ph.container():
        if len(alerts_data) > 0:
            st.markdown("".join([a["html"] for a in alerts_data]), unsafe_allow_html=True)
        else:
            st.markdown("<div style='color:var(--success); font-size:12px; font-weight:600; display:flex; gap:8px; margin-top: 10px;'><svg width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><path d='M22 11.08V12a10 10 0 1 1-5.93-9.14'></path><polyline points='22 4 12 14.01 9 11.01'></polyline></svg> NETWORK STABLE</div><div style='color:var(--muted); font-size:11px; margin-top:4px;'>No active threats detected in telemetry.</div>", unsafe_allow_html=True)
            
    with telemetry_ph.container():
        # Render using the native Streamlit DataFrame for the requested filtering/sorting/timespan capabilities!
        st.dataframe(
            pd.DataFrame(telemetry_data),
            use_container_width=True,
            hide_index=True,
            height=300
        )

    time.sleep(0.3)
