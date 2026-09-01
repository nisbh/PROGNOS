import pandas as pd
import xgboost as xgb
import joblib
import json

def simulate_live_inference():
    print("Loading Master Model...")
    try:
        model = joblib.load("ml/model_fusion.pkl")
    except FileNotFoundError:
        print("Error: ml/model_fusion.pkl not found!")
        return

    # Simulate 3 random 10-second windows of traffic arriving at the backend
    # These match the exact 12 PROGNOS universal features the model expects
    simulated_traffic = pd.DataFrame({
        "connections_per_sec": [10.5, 450.2, 1200.5],
        "syn_rate": [0.1, 10.0, 50.5],
        "avg_packet_size": [200.0, 5000.0, 80000.0],
        "flow_duration_mean": [5.0, 250.0, 600.0],
        "fwd_packets_sum": [100.0, 50.0, 10.0],
        "bwd_packets_sum": [50.0, 10.0, 1.0],
        "flow_packets_s_mean": [500.0, 200.0, 50.0],
        "connections_per_sec_diff": [1.0, 50.0, 500.0],
        "syn_rate_diff": [0.0, 2.5, 10.5],
        "connections_1m_avg": [10.0, 200.0, 800.0],
        "syn_rate_1m_avg": [0.1, 5.0, 20.0],
        "packet_size_1m_avg": [190.0, 4500.0, 75000.0]
    })

    print("\nSimulated Traffic Arriving (3 separate 10s windows):")
    print(simulated_traffic)

    # 1. Generate probabilities for all 4 classes (multi:softprob)
    print("\n--- Model Output (Raw Probabilities) ---")
    probabilities = model.predict_proba(simulated_traffic)
    
    label_map = {0: "NORMAL", 1: "ELEVATED", 2: "NEAR-TERM", 3: "IMMINENT"}
    
    for i, prob_array in enumerate(probabilities):
        print(f"\nWindow {i+1} Raw Array: {prob_array}")
        
        # 2. How the backend processes this raw array:
        max_index = int(prob_array.argmax())
        predicted_label = label_map[max_index]
        confidence = float(prob_array[max_index]) * 100
        
        # 3. Formatted for the Frontend (JSON)
        backend_response = {
            "window_id": i + 1,
            "prediction": predicted_label,
            "confidence": f"{confidence:.2f}%",
            "full_distribution": {
                "NORMAL": f"{prob_array[0]*100:.2f}%",
                "ELEVATED": f"{prob_array[1]*100:.2f}%",
                "NEAR-TERM": f"{prob_array[2]*100:.2f}%",
                "IMMINENT": f"{prob_array[3]*100:.2f}%"
            }
        }
        print("Backend JSON sent to Frontend:")
        print(json.dumps(backend_response, indent=2))

if __name__ == "__main__":
    simulate_live_inference()
