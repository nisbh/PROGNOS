import pandas as pd
import numpy as np
import os
import glob
import time

def generate_unsw_data():
    data_dir = r"N:\Github Projects\PROGNOS\data\CSV Files"
    csv_files = glob.glob(os.path.join(data_dir, "UNSW-NB15_[1-4].csv"))
    
    if not csv_files:
        print(f"No UNSW-NB15 CSV files found in {data_dir}")
        return

    columns = [
        'srcip', 'sport', 'dstip', 'dsport', 'proto', 'state', 'dur', 'sbytes', 'dbytes',
        'sttl', 'dttl', 'sloss', 'dloss', 'service', 'Sload', 'Dload', 'Spkts', 'Dpkts',
        'swin', 'dwin', 'stcpb', 'dtcpb', 'smeansz', 'dmeansz', 'trans_depth', 'res_bdy_len',
        'Sjit', 'Djit', 'Stime', 'Ltime', 'Sintpkt', 'Dintpkt', 'tcprtt', 'synack', 'ackdat',
        'is_sm_ips_ports', 'ct_state_ttl', 'ct_flw_http_mthd', 'is_ftp_login', 'ct_ftp_cmd',
        'ct_srv_src', 'ct_srv_dst', 'ct_dst_ltm', 'ct_src_ltm', 'ct_src_dport_ltm',
        'ct_dst_sport_ltm', 'ct_dst_src_ltm', 'attack_cat', 'Label'
    ]

    all_windows = []

    for file_path in csv_files:
        print(f"\nProcessing {os.path.basename(file_path)}...")
        try:
            # UNSW-NB15 has no header row in the main CSVs
            df = pd.read_csv(file_path, names=columns, low_memory=False)
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
            continue
            
        print("Parsing timestamps...")
        # Stime is Unix timestamp
        df['Timestamp'] = pd.to_datetime(df['Stime'], unit='s', errors='coerce')
        df = df.dropna(subset=['Timestamp'])
        
        # Sort by timestamp
        df = df.sort_values('Timestamp')
        df = df.set_index('Timestamp')
        
        print("Mapping features to PROGNOS format...")
        # Map UNSW-NB15 to our 8 core features
        # 1. Flow Duration (dur)
        # 2. Total Fwd Packets (Spkts)
        # 3. Total Bwd Packets (Dpkts)
        # 4. Average Packet Size = (sbytes + dbytes) / (Spkts + Dpkts)
        df['TotalPackets'] = df['Spkts'] + df['Dpkts']
        df['TotalBytes'] = df['sbytes'] + df['dbytes']
        df['Average Packet Size'] = (df['TotalBytes'] / df['TotalPackets']).fillna(0)
        
        # 5. Flow Packets/s = TotalPackets / dur (avoid div by zero)
        df['Flow Packets/s'] = df['TotalPackets'] / df['dur'].replace(0, 0.0001)
        
        # 6. SYN Flag Count equivalent (rough approximation: state == 'CON' or 'REQ')
        # UNSW doesn't have raw TCP flags, but 'state' shows connection attempts. 
        df['SYN_equivalent'] = df['state'].apply(lambda x: 1 if str(x).upper() in ['REQ', 'CON', 'INT'] else 0)
        
        # 7. is_attack_flow
        df['is_attack_flow'] = pd.to_numeric(df['Label'], errors='coerce').fillna(0)
        
        print("Grouping into 10-second rolling windows...")
        agg_df = df.resample('10s').agg(
            connections_per_sec=('Label', 'count'),
            syn_rate=('SYN_equivalent', 'sum'),
            avg_packet_size=('Average Packet Size', 'mean'),
            flow_duration_mean=('dur', 'mean'),
            fwd_packets_sum=('Spkts', 'sum'),
            bwd_packets_sum=('Dpkts', 'sum'),
            flow_packets_s_mean=('Flow Packets/s', 'mean'),
            attack_active=('is_attack_flow', 'max')
        )
        
        agg_df['connections_per_sec'] = agg_df['connections_per_sec'] / 10.0
        agg_df['syn_rate'] = agg_df['syn_rate'] / 10.0
        agg_df = agg_df.fillna(0)
        
        print("Calculating temporal trend features (rolling means & derivatives)...")
        agg_df['connections_per_sec_diff'] = agg_df['connections_per_sec'].diff().fillna(0)
        agg_df['syn_rate_diff'] = agg_df['syn_rate'].diff().fillna(0)
        
        agg_df['connections_1m_avg'] = agg_df['connections_per_sec'].rolling(window=6, min_periods=1).mean()
        agg_df['syn_rate_1m_avg'] = agg_df['syn_rate'].rolling(window=6, min_periods=1).mean()
        agg_df['packet_size_1m_avg'] = agg_df['avg_packet_size'].rolling(window=6, min_periods=1).mean()
        
        print("Calculating lookahead temporal labels...")
        attack_times = agg_df[agg_df['attack_active'] == 1].index
        labels = []
        
        for current_time in agg_df.index:
            is_active = agg_df.loc[current_time, 'attack_active']
            if is_active == 1:
                labels.append("IMMINENT")
                continue
                
            future_attacks = attack_times[attack_times > current_time]
            if len(future_attacks) == 0:
                labels.append("NORMAL")
                continue
                
            next_attack_time = future_attacks[0]
            time_to_attack = (next_attack_time - current_time).total_seconds()
            
            if time_to_attack <= 30:
                labels.append("IMMINENT")
            elif time_to_attack <= 120:
                labels.append("NEAR-TERM")
            elif time_to_attack <= 300:
                labels.append("ELEVATED")
            else:
                labels.append("NORMAL")
                
        agg_df['label'] = labels
        all_windows.append(agg_df)

    print("\nMerging all days (parts)...")
    final_df = pd.concat(all_windows, ignore_index=True)
    
    print(f"Total windows before balancing: {len(final_df)}")
    print(final_df['label'].value_counts())
    
    print("Balancing classes (Downsampling NORMAL and massive IMMINENT attacks)...")
    normal_df = final_df[final_df['label'] == 'NORMAL']
    elevated_df = final_df[final_df['label'] == 'ELEVATED']
    near_term_df = final_df[final_df['label'] == 'NEAR-TERM']
    imminent_df = final_df[final_df['label'] == 'IMMINENT']
    
    target_size = max(len(elevated_df), len(near_term_df)) * 5
    
    if len(normal_df) > target_size and target_size > 0:
        normal_df = normal_df.sample(n=target_size, random_state=42)
        
    if len(imminent_df) > target_size and target_size > 0:
        imminent_df = imminent_df.sample(n=target_size, random_state=42)
        
    balanced_df = pd.concat([normal_df, elevated_df, near_term_df, imminent_df])
    
    print(f"Final dataset size: {len(balanced_df)} windows")
    print("Class distribution:")
    print(balanced_df['label'].value_counts())
    
    out_path = r"N:\Github Projects\PROGNOS\data\training_features_unsw.csv"
    balanced_df.to_csv(out_path, index=False)
    print(f"\nSaved perfectly balanced multi-day dataset to {out_path}!")

if __name__ == "__main__":
    generate_unsw_data()
