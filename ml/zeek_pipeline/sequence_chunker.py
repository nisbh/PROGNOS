import pandas as pd
import numpy as np
import argparse
from pathlib import Path

def parse_zeek_log(log_path):
    """Parses Zeek TSV logs with comments, extracting headers dynamically."""
    with open(log_path, 'r') as f:
        lines = f.readlines()
        
    fields = []
    for line in lines:
        if line.startswith('#fields'):
            fields = line.strip().split('\t')[1:]
            break
            
    df = pd.read_csv(log_path, sep='\t', comment='#', names=fields)
    return df

def create_time_series_sequences(df, window_seconds=10):
    """Chunks network connections into sequential time-windows."""
    # Convert timestamp to datetime (Zeek logs epoch seconds)
    df['ts'] = pd.to_datetime(df['ts'], unit='s')
    
    # Sort chronologically
    df = df.sort_values('ts')
    
    # Set time as index for pandas resampling
    df.set_index('ts', inplace=True)
    
    # Identify numeric columns for aggregation
    numeric_cols = [
        'duration', 'orig_bytes', 'resp_bytes', 'orig_pkts', 'resp_pkts',
        'min_ttl_orig', 'max_ttl_orig', 'min_ttl_resp', 'max_ttl_resp',
        'avg_win_orig', 'avg_win_resp',
        'payload_min_orig', 'payload_max_orig', 'payload_min_resp', 'payload_max_resp',
        'frag_count', 'retrans_orig', 'retrans_resp',
        'flag_syn', 'flag_ack', 'flag_fin', 'flag_rst', 'flag_psh', 'flag_urg',
        'iat_mean', 'iat_max', 'iat_var'
    ]
    
    # Handle Zeek's '-' null values and coerce to floats
    for col in numeric_cols:
        if col in df.columns:
            # Replace '-' with NaN, then convert to numeric
            df[col] = pd.to_numeric(df[col].replace('-', np.nan), errors='coerce').fillna(0)
            
    # Define aggregation rules: mean of features across the 10s window
    agg_dict = {col: 'mean' for col in numeric_cols if col in df.columns}
    
    # Count the number of unique connections/flows in this window
    if 'uid' in df.columns:
        agg_dict['uid'] = 'count'
        
    # Extract port scan signatures (unique destination ports in the 10s window)
    if 'id.resp_p' in df.columns:
        agg_dict['id.resp_p'] = 'nunique'
    
    # Perform the resample and fill empty windows with 0
    resampled = df.resample(f'{window_seconds}s').agg(agg_dict).fillna(0)
    
    # Rename columns to something more descriptive
    rename_dict = {}
    if 'uid' in resampled.columns:
        rename_dict['uid'] = 'flow_count'
    if 'id.resp_p' in resampled.columns:
        rename_dict['id.resp_p'] = 'unique_dest_ports_scan_signature'
        
    resampled.rename(columns=rename_dict, inplace=True)
    
    # Calculate bidirectional flow ratio
    if 'orig_bytes' in resampled.columns and 'resp_bytes' in resampled.columns:
        resampled['bidirectional_flow_ratio'] = resampled['orig_bytes'] / (resampled['resp_bytes'] + 1e-9)
        
    return resampled

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Chunk Zeek logs into sequential time-series windows.")
    parser.add_argument('--input', type=str, required=True, help="Path to prognos_features.log")
    parser.add_argument('--output', type=str, required=True, help="Path to save output CSV (e.g., sequences.csv)")
    parser.add_argument('--window', type=int, default=10, help="Window size in seconds (default 10)")
    
    args = parser.parse_args()
    
    print(f"Parsing Zeek log: {args.input}")
    try:
        df = parse_zeek_log(args.input)
    except Exception as e:
        print(f"Error parsing log file: {e}")
        exit(1)
        
    print(f"Chunking into {args.window}-second windows...")
    sequence_df = create_time_series_sequences(df, window_seconds=args.window)
    
    sequence_df.to_csv(args.output)
    print(f"Saved {len(sequence_df)} sequence windows to {args.output}")
