from fastapi import FastAPI
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

def generate_traffic_state(tick: int) -> pd.DataFrame:
    """Generates a Pandas DataFrame of the 12 features based on the current attack stage."""
    # Cycle resets every 10 ticks (100 seconds)
    stage = tick % 10
    
    if stage < 3:
        # NORMAL
        data = [10 + random.uniform(-2, 2), 0.1, 200, 5, 100, 50, 500, 1, 0, 10, 0.1, 190]
    elif stage < 5:
        # ELEVATED (Traffic starts rising)
        data = [150 + random.uniform(-20, 20), 5.0, 1000, 50, 80, 40, 400, 20, 1.5, 50, 2.0, 500]
    elif stage < 7:
        # NEAR-TERM (Heavy SYN scanning)
        data = [450 + random.uniform(-50, 50), 25.0, 5000, 250, 50, 10, 200, 50, 5.0, 200, 10.0, 4500]
    else:
        # IMMINENT (Full scale DDoS)
        data = [1200 + random.uniform(-100, 100), 75.0, 80000, 600, 10, 1, 50, 500, 15.0, 800, 40.0, 75000]
        
    df = pd.DataFrame([data], columns=FEATURE_NAMES)
    return df

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

async def background_simulation_loop():
    """Background task that ticks the simulation forward every 10 seconds."""
    global SIMULATION_TICK, HISTORY_LOG, TRAFFIC_HISTORY
    while True:
        # 1. Generate new traffic data for this tick
        current_df = generate_traffic_state(SIMULATION_TICK)
        
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
            
        # Update Traffic chart history
        TRAFFIC_HISTORY.insert(0, {
            "timestamp": ts,
            "connections_per_sec": float(current_df.iloc[0]["connections_per_sec"]),
            "syn_rate": float(current_df.iloc[0]["syn_rate"])
        })
        
        if len(TRAFFIC_HISTORY) > 20:
            TRAFFIC_HISTORY.pop()
            
        print(f"[Simulation Tick {SIMULATION_TICK}] Predicted: {pred_class} ({conf*100:.1f}%)")
        SIMULATION_TICK += 1
        
        # Wait 10 seconds before generating the next traffic window
        await asyncio.sleep(10)

@app.on_event("startup")
async def startup_event():
    # Pre-populate history with 5 normal ticks so the dashboard isn't empty on load
    for i in range(5):
        df = generate_traffic_state(0)
        pred_class, conf, probs, top_features = run_ml_inference(df)
        ts = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(seconds=(5-i)*10)).isoformat()
        HISTORY_LOG.insert(0, {
            "ts": ts,
            "class": pred_class,
            "confidence": conf,
            "probs": probs,
            "top_features": top_features
        })
        TRAFFIC_HISTORY.insert(0, {
            "timestamp": ts,
            "connections_per_sec": float(df.iloc[0]["connections_per_sec"]),
            "syn_rate": float(df.iloc[0]["syn_rate"])
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
    
    if risk_class != "NORMAL":
        # Let's map dynamically. If syn_rate is highest, it's SYN flood. If connections_per_sec, generic DoS.
        top_feature_name = latest["top_features"][0]["name"] if latest["top_features"] else ""
        if "syn" in top_feature_name.lower() and "SYN Flood" in MITRE_DB:
            response["mitre_context"] = MITRE_DB["SYN Flood"]
        elif "DoS GoldenEye" in MITRE_DB:
            response["mitre_context"] = MITRE_DB["DoS GoldenEye"]
            
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
