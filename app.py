import streamlit as st
import pandas as pd
import numpy as np
import torch
import altair as alt
import time
import sys
import os

# Add ml folder to path so we can import the model
sys.path.append(os.path.join(os.path.dirname(__file__), 'ml'))
from world_model import PrognosWorldModel
from dataset import get_dataloader

# ==========================================
# PAGE CONFIGURATION
# ==========================================
st.set_page_config(
    page_title="PROGNOS Network Security",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Professional, Sober CSS
st.markdown("""
<style>
    .main {background-color: #F8F9FA;}
    h1, h2, h3 {color: #2C3E50 !important; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;}
    .metric-card {
        background-color: #FFFFFF;
        border-radius: 4px;
        padding: 20px;
        border: 1px solid #E2E8F0;
        border-left: 5px solid #34495E;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .metric-title {
        color: #7F8C8D;
        font-size: 14px;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 10px;
    }
    .metric-value {
        color: #2C3E50;
        font-size: 28px;
        font-weight: bold;
    }
    .stProgress > div > div > div > div {
        background-color: #3498DB;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# CACHING & MODEL LOADING
# ==========================================
@st.cache_resource
def load_world_model():
    model = PrognosWorldModel(input_features=30, num_classes=5)
    weights_path = os.path.join(os.path.dirname(__file__), 'ml', 'world_model_weights.pt')
    if os.path.exists(weights_path):
        model.load_state_dict(torch.load(weights_path, map_location=torch.device('cpu')))
    model.eval()
    return model

@st.cache_data
def process_data(csv_path):
    # Using is_train=True temporarily so it fits a scaler on the uploaded file.
    # In production (Phase 5), we will load a pre-fitted scaler.pkl here.
    loader, scaler = get_dataloader(csv_path, batch_size=1, sequence_length=6, is_train=True)
    raw_df = pd.read_csv(csv_path)
    return loader, raw_df

# ==========================================
# MAIN DASHBOARD
# ==========================================
st.title("PROGNOS Threat Analysis System")
st.markdown("Advanced Persistent Threat (APT) Detection via State Transition Modeling")
st.markdown("---")

# Move uploader to main content area
col_upload, col_empty = st.columns([1, 2])
with col_upload:
    upload_file = st.file_uploader("Upload Network Telemetry (sequences.csv)", type="csv")
    run_inference = st.button("Initialize Analysis", use_container_width=True)

# MITRE ATT&CK Mapping (Professional Colors)
mitre_map = {
    0: ("Normal Traffic", "#27AE60"),       # Green
    1: ("Reconnaissance", "#F1C40F"),       # Yellow
    2: ("Initial Access", "#E67E22"),       # Orange
    3: ("Lateral Movement", "#D35400"),     # Dark Orange
    4: ("Command & Control", "#C0392B")     # Dark Red
}

if upload_file is not None and run_inference:
    temp_path = "temp_sequences.csv"
    with open(temp_path, "wb") as f:
        f.write(upload_file.getbuffer())
        
    model = load_world_model()
    loader, raw_df = process_data(temp_path)
    
    st.markdown("### Active Trajectory Simulation")
    progress_bar = st.progress(0)
    
    col1, col2, col3 = st.columns(3)
    metric_prob = col1.empty()
    metric_mitre = col2.empty()
    metric_ip = col3.empty()
    
    chart_placeholder = st.empty()
    time_series_data = pd.DataFrame(columns=["Time Window", "Infiltration Probability"])
    
    for idx, (x, y_mitre, y_prob) in enumerate(loader):
        with torch.no_grad():
            mitre_logits, prob_preds, attn_weights = model(x)
            
        prob_val = prob_preds.item() * 100
        stage_idx = torch.argmax(mitre_logits, dim=1).item()
        stage_name, stage_color = mitre_map[stage_idx]
        
        suspect_ip = raw_df.iloc[idx]['id.orig_h'] if 'id.orig_h' in raw_df.columns else "Unknown"
        
        metric_prob.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Infiltration Probability</div>
            <div class="metric-value" style="color: {stage_color};">{prob_val:.1f}%</div>
        </div>
        """, unsafe_allow_html=True)
        
        metric_mitre.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Predicted MITRE Stage</div>
            <div class="metric-value" style="color: {stage_color};">{stage_name}</div>
        </div>
        """, unsafe_allow_html=True)
        
        metric_ip.markdown(f"""
        <div class="metric-card" style="border-left: 5px solid #2980B9;">
            <div class="metric-title">Primary Target / Actor IP</div>
            <div class="metric-value">{suspect_ip}</div>
        </div>
        """, unsafe_allow_html=True)
        
        new_row = pd.DataFrame({"Time Window": [idx], "Infiltration Probability": [prob_val]})
        time_series_data = pd.concat([time_series_data, new_row], ignore_index=True)
        
        line_chart = alt.Chart(time_series_data).mark_area(
            line={'color':'#2980B9'},
            color=alt.Gradient(
                gradient='linear',
                stops=[alt.GradientStop(color='#3498DB', offset=0),
                       alt.GradientStop(color='rgba(255,255,255,0)', offset=1)],
                x1=1, x2=1, y1=1, y2=0
            )
        ).encode(
            x=alt.X('Time Window:Q', axis=alt.Axis(grid=False)),
            y=alt.Y('Infiltration Probability:Q', scale=alt.Scale(domain=[0, 100]), axis=alt.Axis(grid=True))
        ).properties(height=300)
        
        chart_placeholder.altair_chart(line_chart, use_container_width=True)
        
        time.sleep(0.05)
        progress_bar.progress((idx + 1) / len(loader))
        
        if idx > 200:
            break
            
    st.markdown("---")
    st.markdown("**Status:** Simulation Complete.")
