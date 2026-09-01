import pandas as pd
import random
import os

FEATURE_NAMES = [
    "connections_per_sec", "syn_rate", "avg_packet_size", "flow_duration_mean",
    "fwd_packets_sum", "bwd_packets_sum", "flow_packets_s_mean",
    "connections_per_sec_diff", "syn_rate_diff", "connections_1m_avg",
    "syn_rate_1m_avg", "packet_size_1m_avg"
]

def generate_chronological_demo_csv(filepath: str):
    rows = []
    # Generate 100 chronological ticks
    for tick in range(100):
        stage = tick % 10
        
        if stage < 3:
            # NORMAL
            data = [10 + random.uniform(-2, 2), 0.1, 200, 5, 100, 50, 500, 1, 0, 10, 0.1, 190]
        elif stage < 5:
            # ELEVATED
            data = [150 + random.uniform(-20, 20), 5.0, 1000, 50, 80, 40, 400, 20, 1.5, 50, 2.0, 500]
        elif stage < 7:
            # NEAR-TERM
            data = [450 + random.uniform(-50, 50), 25.0, 5000, 250, 50, 10, 200, 50, 5.0, 200, 10.0, 4500]
        else:
            # IMMINENT
            data = [1200 + random.uniform(-100, 100), 75.0, 80000, 600, 10, 1, 50, 500, 15.0, 800, 40.0, 75000]
            
        rows.append(data)
        
    df = pd.DataFrame(rows, columns=FEATURE_NAMES)
    
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    df.to_csv(filepath, index=False)
    print(f"Created {filepath} with {len(df)} sequential rows for live replay.")

if __name__ == "__main__":
    generate_chronological_demo_csv("data/demo_replay.csv")
