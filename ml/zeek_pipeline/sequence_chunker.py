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
        'avg_win_orig', 'avg_win_resp'
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
    
    # Perform the resample and fill empty windows with 0
    resampled = df.resample(f'{window_seconds}s').agg(agg_dict).fillna(0)
    
    # Rename uid count to something more descriptive
    if 'uid' in resampled.columns:
        resampled.rename(columns={'uid': 'flow_count'}, inplace=True)
        
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
