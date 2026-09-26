"""
create_demo_csv.py
==================
Generates a demo sequences CSV that simulates a realistic CIC-IDS-2018
attack progression: Normal → Reconnaissance → Initial Access → C2.

This demo CSV is used by the PROGNOS dashboard's "Load Demo Dataset" button.
Run once before the demo:

    python create_demo_csv.py

Output: data/demo_sequences.csv
"""

import pandas as pd
import numpy as np
import os

np.random.seed(42)
os.makedirs("data", exist_ok=True)

FEATURE_COLS = [
    'duration', 'orig_bytes', 'resp_bytes', 'orig_pkts', 'resp_pkts',
    'min_ttl_orig', 'max_ttl_orig', 'min_ttl_resp', 'max_ttl_resp',
    'avg_win_orig', 'avg_win_resp', 'payload_min_orig', 'payload_max_orig',
    'payload_min_resp', 'payload_max_resp', 'frag_count', 'retrans_orig',
    'retrans_resp', 'flag_syn', 'flag_ack', 'flag_fin', 'flag_rst',
    'flag_psh', 'flag_urg', 'iat_mean', 'iat_max', 'iat_var',
    'flow_count', 'unique_dest_ports_scan_signature', 'bidirectional_flow_ratio'
]


def generate_phase(n_rows, phase: str, ip: str, start_ts: pd.Timestamp):
    """Generate synthetic traffic rows for one phase of an attack."""
    rows = []
    ts = start_ts
    for _ in range(n_rows):
        row = {'id.orig_h': ip, 'ts': ts}

        if phase == 'normal':
            row.update({
                'duration': np.random.uniform(0.01, 1.5),
                'orig_bytes': np.random.randint(200, 3000),
                'resp_bytes': np.random.randint(300, 8000),
                'orig_pkts': np.random.randint(2, 20),
                'resp_pkts': np.random.randint(2, 25),
                'flag_syn': np.random.randint(0, 2),
                'flag_ack': 1,
                'flag_fin': np.random.randint(0, 2),
                'flag_rst': 0,
                'flag_psh': np.random.randint(0, 2),
                'flag_urg': 0,
                'flow_count': np.random.randint(1, 8),
                'unique_dest_ports_scan_signature': np.random.randint(1, 3),
                'iat_mean': np.random.uniform(0.05, 0.5),
                'iat_max': np.random.uniform(0.1, 1.0),
                'iat_var': np.random.uniform(0.01, 0.1),
                'bidirectional_flow_ratio': np.random.uniform(0.4, 0.6),
            })

        elif phase == 'recon':
            row.update({
                'duration': np.random.uniform(0.001, 0.05),
                'orig_bytes': np.random.randint(40, 100),
                'resp_bytes': np.random.randint(0, 60),
                'orig_pkts': np.random.randint(1, 4),
                'resp_pkts': np.random.randint(0, 3),
                'flag_syn': 1,
                'flag_ack': 0,
                'flag_fin': 0,
                'flag_rst': np.random.randint(0, 2),
                'flag_psh': 0,
                'flag_urg': 0,
                'flow_count': np.random.randint(30, 80),
                'unique_dest_ports_scan_signature': np.random.randint(20, 60),
                'iat_mean': np.random.uniform(0.001, 0.02),
                'iat_max': np.random.uniform(0.01, 0.1),
                'iat_var': np.random.uniform(0.001, 0.02),
                'bidirectional_flow_ratio': np.random.uniform(0.8, 1.0),
            })

        elif phase == 'access':
            row.update({
                'duration': np.random.uniform(0.1, 2.0),
                'orig_bytes': np.random.randint(500, 5000),
                'resp_bytes': np.random.randint(100, 1000),
                'orig_pkts': np.random.randint(10, 50),
                'resp_pkts': np.random.randint(2, 15),
                'flag_syn': np.random.randint(3, 10),
                'flag_ack': np.random.randint(5, 20),
                'flag_fin': 0,
                'flag_rst': np.random.randint(1, 5),
                'flag_psh': np.random.randint(2, 8),
                'flag_urg': 0,
                'flow_count': np.random.randint(15, 40),
                'unique_dest_ports_scan_signature': np.random.randint(2, 8),
                'iat_mean': np.random.uniform(0.01, 0.15),
                'iat_max': np.random.uniform(0.05, 0.5),
                'iat_var': np.random.uniform(0.005, 0.05),
                'bidirectional_flow_ratio': np.random.uniform(0.6, 0.9),
            })

        elif phase == 'c2':
            row.update({
                'duration': np.random.uniform(5, 60),
                'orig_bytes': np.random.randint(100, 500),
                'resp_bytes': np.random.randint(50, 300),
                'orig_pkts': np.random.randint(5, 20),
                'resp_pkts': np.random.randint(3, 15),
                'flag_syn': np.random.randint(0, 3),
                'flag_ack': 1,
                'flag_fin': 0,
                'flag_rst': 0,
                'flag_psh': np.random.randint(1, 4),
                'flag_urg': 0,
                'flow_count': np.random.randint(5, 15),
                'unique_dest_ports_scan_signature': 1,
                'iat_mean': np.random.uniform(1.0, 5.0),
                'iat_max': np.random.uniform(5, 20),
                'iat_var': np.random.uniform(0.5, 2.0),
                'bidirectional_flow_ratio': np.random.uniform(0.3, 0.6),
            })

        # Fill missing feature cols with 0
        for col in FEATURE_COLS:
            if col not in row:
                row[col] = 0.0

        rows.append(row)
        ts += pd.Timedelta(seconds=10)

    return pd.DataFrame(rows)


# Build the demo scenario
BASE_TS = pd.Timestamp("2018-02-14 09:00:00")

dfs = []

# Benign client
dfs.append(generate_phase(60, 'normal',  '172.31.2.10', BASE_TS))

# Attacker IP: progresses through all stages
attacker_ip = '18.219.9.1'
ts = BASE_TS
dfs.append(generate_phase(30, 'normal', attacker_ip, ts));  ts += pd.Timedelta(minutes=5)
dfs.append(generate_phase(25, 'recon',  attacker_ip, ts));  ts += pd.Timedelta(minutes=4, seconds=10)
dfs.append(generate_phase(25, 'access', attacker_ip, ts));  ts += pd.Timedelta(minutes=4, seconds=10)
dfs.append(generate_phase(40, 'c2',     attacker_ip, ts))

# Another normal client for volume
dfs.append(generate_phase(50, 'normal', '172.31.3.55', BASE_TS + pd.Timedelta(minutes=2)))

demo_df = pd.concat(dfs, ignore_index=True)
demo_df = demo_df.sort_values(['id.orig_h', 'ts']).reset_index(drop=True)

output_path = "data/demo_sequences.csv"
demo_df.to_csv(output_path, index=False)

print(f"✅ Demo CSV created: {output_path}")
print(f"   Total rows   : {len(demo_df):,}")
print(f"   Unique IPs   : {demo_df['id.orig_h'].nunique()}")
print(f"   Time range   : {demo_df['ts'].min()} → {demo_df['ts'].max()}")
print(f"\n   Attacker IP  : {attacker_ip}")
print(f"   Phase sequence: Normal → Reconnaissance → Initial Access → C2")
