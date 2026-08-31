from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import datetime
import random

app = FastAPI(title="PROGNOS Attack Forecasting API")

# Enable CORS for the React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Mock Data Generation ---
# In a real implementation, these would query the ML model state or database
MOCK_CLASSES = ["NORMAL", "ELEVATED", "NEAR-TERM", "IMMINENT"]
current_class_idx = 1 # Start at ELEVATED for testing

@app.get("/current-status")
def get_current_status():
    """Returns the current overall risk assessment."""
    risk_class = MOCK_CLASSES[current_class_idx]
    # Map class to a rough score
    score_map = {"NORMAL": 10, "ELEVATED": 45, "NEAR-TERM": 75, "IMMINENT": 95}
    base_score = score_map[risk_class]
    
    return {
        "risk_level": risk_class,
        "risk_score": base_score + random.randint(-5, 5), # Add some jitter
        "class": risk_class,
        "ts": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }

@app.get("/forecast")
def get_forecast():
    """Returns the model's detailed forecast."""
    risk_class = MOCK_CLASSES[current_class_idx]
    prob_map = {"NORMAL": 0.1, "ELEVATED": 0.45, "NEAR-TERM": 0.75, "IMMINENT": 0.95}
    
    return {
        "class": risk_class,
        "probability": prob_map[risk_class] + random.uniform(-0.05, 0.05),
        "eta_window": "2m-5m" if risk_class == "ELEVATED" else "30s-2m" if risk_class == "NEAR-TERM" else "0s-30s" if risk_class == "IMMINENT" else "N/A",
        "top_features": ["SYN_rate_slope", "unique_source_ips_pct_change", "connection_count"]
    }

@app.get("/traffic")
def get_traffic():
    """Returns recent window stats for the trend chart."""
    # Generate 10 mock points
    now = datetime.datetime.now(datetime.timezone.utc)
    points = []
    for i in range(10, 0, -1):
        ts = (now - datetime.timedelta(seconds=i*10)).isoformat()
        points.append({
            "timestamp": ts,
            "connections_per_sec": random.randint(100, 500) if current_class_idx < 2 else random.randint(1000, 5000),
            "syn_rate": random.randint(10, 50) if current_class_idx < 2 else random.randint(500, 2000)
        })
    return {"history": points}

@app.get("/explanation")
def get_explanation():
    """Returns SHAP top features for the current prediction."""
    return {
        "features": [
            {"name": "SYN_rate_slope", "shap_value": round(random.uniform(0.5, 2.5), 2), "actual_value": "+450%"},
            {"name": "unique_source_ips_pct_change", "shap_value": round(random.uniform(0.2, 1.5), 2), "actual_value": "+120%"},
            {"name": "connection_count_rolling_mean", "shap_value": round(random.uniform(0.1, 1.0), 2), "actual_value": "850"}
        ]
    }

@app.get("/history")
def get_history(limit: int = 5):
    """Returns the last N window classifications."""
    now = datetime.datetime.now(datetime.timezone.utc)
    history = []
    for i in range(limit, 0, -1):
        ts = (now - datetime.timedelta(seconds=i*10)).isoformat()
        # Mock past states (slowly ramping up)
        hist_class = MOCK_CLASSES[max(0, current_class_idx - (i // 2))] 
        history.append({
            "ts": ts,
            "class": hist_class
        })
    return {"history": history}

# To run: uv run uvicorn main:app --reload
