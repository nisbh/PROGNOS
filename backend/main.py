from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import datetime
import random
import json
import os
import asyncio

import joblib
import pandas as pd
import numpy as np
import shap

app = FastAPI(title="PROGNOS Attack Forecasting API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MOCK_CLASSES = ["NORMAL", "ELEVATED", "NEAR-TERM", "IMMINENT"]

MITRE_DB = {}
mitre_path = os.path.join(os.path.dirname(__file__), "mitre_mapping.json")
if os.path.exists(mitre_path):
    with open(mitre_path, "r") as f:
        MITRE_DB = json.load(f).get("attacks", {})

# --- ML State ---
MODEL = None
LABEL_MAP = None
EXPLAINER = None
IS_READY = False

model_path = os.path.join(os.path.dirname(__file__), "..", "ml", "model_fusion.pkl")

print("Loading ML model...")
if os.path.exists(model_path):
    try:
        MODEL = joblib.load(model_path)
        LABEL_MAP = {0: "NORMAL", 1: "ELEVATED", 2: "NEAR-TERM", 3: "IMMINENT"}
        # Initialize SHAP tree explainer
        EXPLAINER = shap.TreeExplainer(MODEL)
        IS_READY = True
        print("ML model and SHAP explainer loaded successfully.")
    except Exception as e:
        print(f"Could not load ML model: {e}")
else:
    print(f"ML model not found at {model_path}. Using fallback mock logic.")

# --- Live Simulation State ---
# We will simulate a continuous stream of traffic that slowly builds up to a DDoS attack
# over 60 seconds (6 ticks of 10s each), then loops back to normal.
SIMULATION_TICK = 0
HISTORY_LOG = []
TRAFFIC_HISTORY = []

# 12 universal PROGNOS features
FEATURE_NAMES = [
    "connections_per_sec", "syn_rate", "avg_packet_size", "flow_duration_mean",
    "fwd_packets_sum", "bwd_packets_sum", "flow_packets_s_mean",
    "connections_per_sec_diff", "syn_rate_diff", "connections_1m_avg",
    "syn_rate_1m_avg", "packet_size_1m_avg"
]

def get_traffic_state_from_csv(tick: int, df_replay: pd.DataFrame) -> pd.DataFrame:
    """Reads the current tick's row from the CSV file."""
    # Loop back to start if we reach the end of the CSV
    row_idx = tick % len(df_replay)
    row_data = df_replay.iloc[[row_idx]]
    return row_data

def run_ml_inference(df: pd.DataFrame):
    """Runs the model and SHAP explainer on the given dataframe."""
    if not IS_READY:
        return MOCK_CLASSES[0], 0.99, [1.0, 0, 0, 0], []
        
    # Get probabilities
    probs = MODEL.predict_proba(df)[0]
    max_index = int(probs.argmax())
    predicted_class = LABEL_MAP[max_index]
    confidence = float(probs[max_index])
    
    # Get SHAP values
    shap_values = EXPLAINER.shap_values(df)
    
    # shap_values might be a list of arrays or a single array (samples, features, classes)
    if isinstance(shap_values, list):
        class_shap = shap_values[max_index][0]
    elif len(shap_values.shape) == 3:
        # Array of shape (1, 12, 4)
        class_shap = shap_values[0, :, max_index]
    else:
        class_shap = shap_values[0]
        
    # Find top 3 contributing features
    # Pair feature names with their absolute shap values to find the biggest impact
    feature_impacts = []
    for i, name in enumerate(FEATURE_NAMES):
        impact = class_shap[i]
        actual_val = df.iloc[0][name]
        feature_impacts.append({
            "name": name,
            "shap_value": float(impact),
            "actual_value": f"{actual_val:.2f}"
        })
        
    # Sort by absolute impact (descending)
    feature_impacts.sort(key=lambda x: abs(x["shap_value"]), reverse=True)
    top_features = feature_impacts[:3]
    
    return predicted_class, confidence, probs.tolist(), top_features

# --- Simulated Multi-Tier Attack Lifecycle Patterns (Fallback Mode) ---
# Cycles through NORMAL -> ELEVATED -> NEAR-TERM -> IMMINENT when no CSV is uploaded
SIMULATION_PATTERNS = [
    # Ticks 0, 1: NORMAL (baseline operational state)
    [15.0, 2.0, 350.0, 50.0, 10.0, 8.0, 20.0, 0.5, 0.1, 15.0, 2.0, 350.0],
    [18.2, 2.5, 380.0, 55.0, 12.0, 9.0, 22.0, 1.2, 0.2, 16.5, 2.2, 360.0],
    # Ticks 2, 3: ELEVATED (early anomalous indicators)
    [22.8, 7.7, 29.0, 16.1, 93.0, 80.8, 63.3, 87.1, 80.4, 18.6, 89.2, 53.9],
    [32.5, 12.4, 65.0, 84.9, 65.8, 56.8, 37.5, 36.8, 26.5, 24.4, 97.3, 39.3],
    # Ticks 4, 5: NEAR-TERM (attack velocity rising)
    [28.5, 3.7, 61.0, 50.3, 5.1, 27.8, 90.8, 24.0, 14.5, 48.9, 98.5, 24.2],
    [37.6, 21.0, 98.7, 15.0, 59.4, 38.1, 96.9, 84.2, 83.8, 46.9, 41.5, 27.3],
    # Ticks 6, 7: IMMINENT (critical saturation attack stage)
    [450.2, 45.0, 5000.0, 250.0, 50.0, 10.0, 200.0, 50.0, 2.5, 200.0, 5.0, 4500.0],
    [850.0, 120.0, 12000.0, 800.0, 150.0, 5.0, 450.0, 400.0, 60.0, 450.0, 65.0, 8000.0]
]

def get_replay_dataframe() -> tuple[pd.DataFrame, bool]:
    """Returns the replay DataFrame and whether a real uploaded CSV is present."""
    csv_path = os.path.join(os.path.dirname(__file__), "..", "data", "demo_replay.csv")
    if os.path.exists(csv_path):
        try:
            df = pd.read_csv(csv_path)
            if len(df) > 0:
                return df, True
        except Exception as e:
            print(f"Error reading CSV at {csv_path}: {e}")
    return pd.DataFrame(SIMULATION_PATTERNS, columns=FEATURE_NAMES), False

# --- Simulated Traffic Fallback State ---
LAST_SIM_CONN = 18.5
LAST_SIM_SYN = 3.2

def generate_smooth_simulated_traffic(last_conn: float = None, last_syn: float = None, target_class: str = "NORMAL") -> tuple[float, float]:
    """Generates smooth, realistic simulated network traffic values based on previous step and threat state."""
    global LAST_SIM_CONN, LAST_SIM_SYN
    
    # Target baseline values by class
    class_targets = {
        "NORMAL": (18.0, 3.0),
        "ELEVATED": (35.0, 12.0),
        "NEAR-TERM": (65.0, 28.0),
        "IMMINENT": (125.0, 65.0)
    }
    target_conn, target_syn = class_targets.get(target_class, (18.0, 3.0))
    
    if last_conn is None or last_conn <= 0:
        last_conn = target_conn
    if last_syn is None or last_syn <= 0:
        last_syn = target_syn
        
    # Gentle step toward target baseline with random micro-variations
    conn_step = (target_conn - last_conn) * 0.35 + random.uniform(-2.5, 2.5)
    new_conn = round(max(8.0, last_conn + conn_step), 1)
    
    syn_step = (target_syn - last_syn) * 0.35 + random.uniform(-0.8, 0.8)
    new_syn = round(max(1.0, last_syn + syn_step), 1)
    
    LAST_SIM_CONN = new_conn
    LAST_SIM_SYN = new_syn
    
    return new_conn, new_syn

async def background_simulation_loop():
    """Background task that ticks the simulation forward every 10 seconds."""
    global SIMULATION_TICK, HISTORY_LOG, TRAFFIC_HISTORY

    while True:
        df_replay, has_real_csv = get_replay_dataframe()
        
        # 1. Read the exact 10s traffic window from the replay dataset
        current_df = get_traffic_state_from_csv(SIMULATION_TICK, df_replay)
        
        # 2. Run Inference
        pred_class, conf, probs, top_features = run_ml_inference(current_df)
        
        # 3. Update History
        ts = datetime.datetime.now(datetime.timezone.utc).isoformat()
        
        HISTORY_LOG.insert(0, {
            "ts": ts,
            "class": pred_class,
            "confidence": conf,
            "probs": probs,
            "top_features": top_features
        })
        
        # Keep only last 100 entries to prevent memory leak
        if len(HISTORY_LOG) > 100:
            HISTORY_LOG.pop()
            
        # Determine traffic values: use real telemetry if available from CSV, otherwise use smooth simulated fallback matching attack state
        raw_conn = float(current_df.iloc[0]["connections_per_sec"])
        raw_syn = float(current_df.iloc[0]["syn_rate"])
        
        if has_real_csv and (raw_conn > 0 or raw_syn > 0):
            conn_val = raw_conn
            syn_val = raw_syn
        else:
            prev_conn = TRAFFIC_HISTORY[0]["connections_per_sec"] if TRAFFIC_HISTORY else 18.5
            prev_syn = TRAFFIC_HISTORY[0]["syn_rate"] if TRAFFIC_HISTORY else 3.2
            conn_val, syn_val = generate_smooth_simulated_traffic(prev_conn, prev_syn, target_class=pred_class)
            
        # Update Traffic chart history
        TRAFFIC_HISTORY.insert(0, {
            "timestamp": ts,
            "connections_per_sec": conn_val,
            "syn_rate": syn_val
        })
        
        if len(TRAFFIC_HISTORY) > 20:
            TRAFFIC_HISTORY.pop()
            
        print(f"[Simulation Tick {SIMULATION_TICK}] State: {pred_class} ({conf*100:.1f}%) | Traffic -> conn: {conn_val}/s, syn: {syn_val}/s")
        SIMULATION_TICK += 1
        
        # Wait 10 seconds before reading the next traffic window
        await asyncio.sleep(10)

@app.on_event("startup")
async def startup_event():
    # Pre-populate history with 5 ticks so the dashboard isn't empty on load
    df_replay, has_real_csv = get_replay_dataframe()
    
    for i in range(5):
        tick_idx = max(0, 5 - 1 - i)
        df = get_traffic_state_from_csv(tick_idx, df_replay)
        pred_class, conf, probs, top_features = run_ml_inference(df)
        ts = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(seconds=(5-i)*10)).isoformat()
        HISTORY_LOG.insert(0, {
            "ts": ts,
            "class": pred_class,
            "confidence": conf,
            "probs": probs,
            "top_features": top_features
        })
        
        raw_conn = float(df.iloc[0]["connections_per_sec"])
        raw_syn = float(df.iloc[0]["syn_rate"])
        if has_real_csv and (raw_conn > 0 or raw_syn > 0):
            conn_val = raw_conn
            syn_val = raw_syn
        else:
            prev_conn = TRAFFIC_HISTORY[0]["connections_per_sec"] if TRAFFIC_HISTORY else 18.5
            prev_syn = TRAFFIC_HISTORY[0]["syn_rate"] if TRAFFIC_HISTORY else 3.2
            conn_val, syn_val = generate_smooth_simulated_traffic(prev_conn, prev_syn, target_class=pred_class)
            
        TRAFFIC_HISTORY.insert(0, {
            "timestamp": ts,
            "connections_per_sec": conn_val,
            "syn_rate": syn_val
        })
        
    asyncio.create_task(background_simulation_loop())



@app.get("/current-status")
def get_current_status():
    if not HISTORY_LOG:
        return {"risk_level": "NORMAL", "risk_score": 0, "class": "NORMAL", "ts": datetime.datetime.now().isoformat()}
        
    latest = HISTORY_LOG[0]
    risk_class = latest["class"]
    score_map = {"NORMAL": 10, "ELEVATED": 45, "NEAR-TERM": 75, "IMMINENT": 95}
    base_score = score_map.get(risk_class, 10)
    
    return {
        "risk_level": risk_class,
        "risk_score": base_score + (latest["confidence"] * 5), 
        "class": risk_class,
        "ts": latest["ts"]
    }

@app.get("/forecast")
def get_forecast():
    if not HISTORY_LOG:
        return {"class": "NORMAL", "probability": 1.0, "eta_window": "N/A", "top_features": []}
        
    latest = HISTORY_LOG[0]
    risk_class = latest["class"]
    
    response = {
        "class": risk_class,
        "probability": latest["confidence"],
        "eta_window": "2m-5m" if risk_class == "ELEVATED" else "30s-2m" if risk_class == "NEAR-TERM" else "0s-30s" if risk_class == "IMMINENT" else "N/A",
        "top_features": [f["name"] for f in latest["top_features"]]
    }
    
    if risk_class != "NORMAL" and latest["top_features"]:
        # Robust multi-feature heuristic mapping
        top_feature_names = [f["name"].lower() for f in latest["top_features"]]
        
        # 1. SYN Flood Check (High SYN rate + high connections)
        if "syn_rate" in top_feature_names and "connections_per_sec" in top_feature_names:
            response["mitre_context"] = MITRE_DB.get("SYN Flood")
            
        # 2. Port Scanning Check (High connections but low/no SYN dominance)
        elif "connections_per_sec" in top_feature_names and "syn_rate" not in top_feature_names:
            response["mitre_context"] = MITRE_DB.get("Port Scanning")
            
        # 3. Application DoS Check (Abnormal packet sizes taking dominance)
        elif "avg_packet_size" in top_feature_names or "packet_size_1m_avg" in top_feature_names:
            response["mitre_context"] = MITRE_DB.get("Application DoS")
            
        # 4. Default to Brute Force if flow durations are perfectly uniform (or catch-all)
        else:
            response["mitre_context"] = MITRE_DB.get("Brute Force")
            
    return response

@app.get("/traffic")
def get_traffic():
    return {"history": TRAFFIC_HISTORY[:10]}

@app.get("/explanation")
def get_explanation():
    if not HISTORY_LOG:
        return {"features": []}
    return {"features": HISTORY_LOG[0]["top_features"]}

@app.get("/history")
def get_history(limit: int = 5):
    # API expects a list of {ts, class}
    formatted = [{"ts": item["ts"], "class": item["class"]} for item in HISTORY_LOG[:limit]]
    return {"history": formatted}

@app.post("/upload-replay")
async def upload_replay(file: UploadFile = File(...)):
    global SIMULATION_TICK, HISTORY_LOG, TRAFFIC_HISTORY
    
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")
        
    csv_path = os.path.join(os.path.dirname(__file__), "..", "data", "demo_replay.csv")
    
    # Save the uploaded file, overwriting the current demo_replay.csv
    with open(csv_path, "wb") as f:
        content = await file.read()
        f.write(content)
        
    # Reset simulation state so the loop restarts from the new file instantly
    SIMULATION_TICK = 0
    HISTORY_LOG.clear()
    TRAFFIC_HISTORY.clear()
    
    # Pre-populate history with 5 normal ticks so the dashboard isn't empty on load
    has_real_csv = os.path.exists(csv_path)
    df_replay = pd.read_csv(csv_path) if has_real_csv else pd.DataFrame([[0]*12], columns=FEATURE_NAMES)
    for i in range(5):
        df = get_traffic_state_from_csv(0, df_replay)
        pred_class, conf, probs, top_features = run_ml_inference(df)
        ts = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(seconds=(5-i)*10)).isoformat()
        HISTORY_LOG.insert(0, {
            "ts": ts,
            "class": pred_class,
            "confidence": conf,
            "probs": probs,
            "top_features": top_features
        })
        
        raw_conn = float(df.iloc[0]["connections_per_sec"])
        raw_syn = float(df.iloc[0]["syn_rate"])
        if has_real_csv and (raw_conn > 0 or raw_syn > 0):
            conn_val = raw_conn
            syn_val = raw_syn
        else:
            prev_conn = TRAFFIC_HISTORY[0]["connections_per_sec"] if TRAFFIC_HISTORY else 18.5
            prev_syn = TRAFFIC_HISTORY[0]["syn_rate"] if TRAFFIC_HISTORY else 3.2
            conn_val, syn_val = generate_smooth_simulated_traffic(prev_conn, prev_syn)
            
        TRAFFIC_HISTORY.insert(0, {
            "timestamp": ts,
            "connections_per_sec": conn_val,
            "syn_rate": syn_val
        })
        
    return {"status": "success", "message": f"Successfully uploaded {file.filename} and restarted simulation."}

