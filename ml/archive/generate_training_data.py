import pandas as pd
import numpy as np
import glob
import os

def generate_multi_day_training_data(csv_dir: str, output_path: str, window_size: str = '10s'):
    print(f"Scanning directory {csv_dir} for CSV files...")
    csv_files = glob.glob(os.path.join(csv_dir, "*.csv"))
    
    if not csv_files:
        print("No CSV files found!")
        return

    all_windows = []
    
    usecols = [
        ' Timestamp', ' Label', ' SYN Flag Count', ' Average Packet Size', 
        ' Flow Duration', ' Total Fwd Packets', ' Total Backward Packets',
        ' Flow Packets/s'
    ]

    for file_path in csv_files:
        print(f"\nProcessing {os.path.basename(file_path)}...")
        try:
            df = pd.read_csv(file_path, usecols=usecols, encoding='cp1252')
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
            continue

        df.columns = df.columns.str.strip()
        
        # Ensure we have the required columns
        if not {'Timestamp', 'Label', 'SYN Flag Count', 'Average Packet Size'}.issubset(set(df.columns)):
            print("Missing required columns, skipping...")
            continue
            
        # Clean Flow Packets/s (sometimes it has Infinity or NaN string)
        if 'Flow Packets/s' in df.columns:
            df['Flow Packets/s'] = pd.to_numeric(df['Flow Packets/s'], errors='coerce').fillna(0)
            # Replace infinities
            df['Flow Packets/s'] = df['Flow Packets/s'].replace([np.inf, -np.inf], 0)
            
        print("Parsing timestamps...")
        # Ignore errors for weird timestamp formats, coerce to NaT and drop
        df['Timestamp'] = pd.to_datetime(df['Timestamp'], format='mixed', dayfirst=True, errors='coerce')
        df = df.dropna(subset=['Timestamp'])
        
        df = df.sort_values('Timestamp')
        df = df.set_index('Timestamp')
        
        # Mark if a flow is an attack (ignoring BENIGN and Normal)
        df['is_attack_flow'] = df['Label'].apply(lambda x: 1 if str(x).upper() not in ['BENIGN', 'NORMAL'] else 0)
        
        print(f"Grouping into {window_size} rolling windows...")
        agg_df = df.resample(window_size).agg(
            connections_per_sec=('Label', 'count'),
            syn_rate=('SYN Flag Count', 'sum'),
            avg_packet_size=('Average Packet Size', 'mean'),
            flow_duration_mean=('Flow Duration', 'mean'),
            fwd_packets_sum=('Total Fwd Packets', 'sum'),
            bwd_packets_sum=('Total Backward Packets', 'sum'),
            flow_packets_s_mean=('Flow Packets/s', 'mean'),
            attack_active=('is_attack_flow', 'max')
        )
        
        seconds = pd.to_timedelta(window_size).total_seconds()
        agg_df['connections_per_sec'] = agg_df['connections_per_sec'] / seconds
        agg_df['syn_rate'] = agg_df['syn_rate'] / seconds
        agg_df = agg_df.fillna(0)
        
        # Drop empty windows to prevent empty traffic artifacts
        # Wait, if we drop them here, we might lose the 30s before an attack if the network is silent.
        # Let's keep them, but fillna.
        agg_df['connections_per_sec'] = agg_df['connections_per_sec'].fillna(0)
        
        print("Calculating temporal trend features (rolling means & derivatives)...")
        # 1. Rate of change (Derivative): How much did this 10s window change compared to the previous 10s window?
        agg_df['connections_per_sec_diff'] = agg_df['connections_per_sec'].diff().fillna(0)
        agg_df['syn_rate_diff'] = agg_df['syn_rate'].diff().fillna(0)
        
        # 2. Moving Average (Trend): What is the 1-minute (6 periods of 10s) moving average?
        agg_df['connections_1m_avg'] = agg_df['connections_per_sec'].rolling(window=6, min_periods=1).mean()
        agg_df['syn_rate_1m_avg'] = agg_df['syn_rate'].rolling(window=6, min_periods=1).mean()
        agg_df['packet_size_1m_avg'] = agg_df['avg_packet_size'].rolling(window=6, min_periods=1).mean()
        
        print("Calculating lookahead temporal labels...")
        # Get all timestamps where an attack is active
        attack_times = agg_df[agg_df['attack_active'] == 1].index
        
        labels = []
        for current_time in agg_df.index:
            is_active = agg_df.loc[current_time, 'attack_active']
            if is_active == 1:
                labels.append("IMMINENT")
                continue
                
            # Find the next attack time that is greater than current_time
            # For massive datasets, doing this cleanly:
            future_attacks = attack_times[attack_times > current_time]
            if len(future_attacks) == 0:
                labels.append("NORMAL")
                continue
                
            time_to_attack = (future_attacks[0] - current_time).total_seconds()
            
            if time_to_attack <= 30:
                labels.append("IMMINENT")
            elif time_to_attack <= 120:
                labels.append("NEAR-TERM")
            elif time_to_attack <= 300:
                labels.append("ELEVATED")
            else:
                labels.append("NORMAL")
                
        agg_df['label'] = labels
        
        # Reset index to make timestamp a column
        agg_df = agg_df.reset_index().rename(columns={'Timestamp': 'timestamp'})
        all_windows.append(agg_df)

    if not all_windows:
        print("No data extracted!")
        return

    print("\nMerging all days...")
    final_df = pd.concat(all_windows, ignore_index=True)
    
    print(f"Total windows before balancing: {len(final_df)}")
    print(final_df['label'].value_counts())
    
    print("Balancing classes (Downsampling NORMAL and massive IMMINENT attacks)...")
    normal_df = final_df[final_df['label'] == 'NORMAL']
    elevated_df = final_df[final_df['label'] == 'ELEVATED']
    near_term_df = final_df[final_df['label'] == 'NEAR-TERM']
    imminent_df = final_df[final_df['label'] == 'IMMINENT']
    
    # We want a reasonable ratio.
    # We will downsample both NORMAL and IMMINENT to prevent them from washing out the forecasting labels.
    target_size = max(len(elevated_df), len(near_term_df)) * 5
    
    if len(normal_df) > target_size and target_size > 0:
        normal_df = normal_df.sample(n=target_size, random_state=42)
        
    if len(imminent_df) > target_size and target_size > 0:
        imminent_df = imminent_df.sample(n=target_size, random_state=42)
        
    balanced_df = pd.concat([normal_df, elevated_df, near_term_df, imminent_df])
    
    # Shuffle the dataset
    balanced_df = balanced_df.sample(frac=1, random_state=42).reset_index(drop=True)
    
    # Drop the temporary attack_active column
    balanced_df = balanced_df.drop(columns=['attack_active'])
    
    print(f"Final dataset size: {len(balanced_df)} windows")
    print("Class distribution:")
    print(balanced_df['label'].value_counts())
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    balanced_df.to_csv(output_path, index=False)
    print(f"\nSaved perfectly balanced multi-day dataset to {output_path}!")

if __name__ == "__main__":
    import sys
    window = sys.argv[1] if len(sys.argv) > 1 else '10s'
    csv_directory = r"N:\Github Projects\PROGNOS\SIH26153\CIC2017\GeneratedLabelledFlows"
    out_file = r"N:\Github Projects\PROGNOS\data\training_features.csv"
    
    generate_multi_day_training_data(csv_directory, out_file, window)
