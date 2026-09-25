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
    df['ts'] = pd.to_datetime(df['ts'], unit='s')
    df = df.sort_values('ts')
    
    numeric_cols = [
        'duration', 'orig_bytes', 'resp_bytes', 'orig_pkts', 'resp_pkts',
        'min_ttl_orig', 'max_ttl_orig', 'min_ttl_resp', 'max_ttl_resp',
        'avg_win_orig', 'avg_win_resp',
        'payload_min_orig', 'payload_max_orig', 'payload_min_resp', 'payload_max_resp',
        'frag_count', 'retrans_orig', 'retrans_resp',
        'flag_syn', 'flag_ack', 'flag_fin', 'flag_rst', 'flag_psh', 'flag_urg',
        'iat_mean', 'iat_max', 'iat_var'
    ]
    
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col].replace('-', np.nan), errors='coerce').fillna(0)
            
    agg_dict = {col: 'mean' for col in numeric_cols if col in df.columns}
    
    if 'uid' in df.columns:
        agg_dict['uid'] = 'count'
        
    if 'id.resp_p' in df.columns:
        agg_dict['id.resp_p'] = 'nunique'
    
    if 'id.orig_h' in df.columns:
        resampled = df.groupby('id.orig_h').resample(f'{window_seconds}s', on='ts').agg(agg_dict).fillna(0)
        resampled = resampled.reset_index()
    else:
        resampled = df.resample(f'{window_seconds}s', on='ts').agg(agg_dict).fillna(0)
        resampled = resampled.reset_index()
    
    rename_dict = {}
    if 'uid' in resampled.columns:
        rename_dict['uid'] = 'flow_count'
    if 'id.resp_p' in resampled.columns:
        rename_dict['id.resp_p'] = 'unique_dest_ports_scan_signature'
        
    resampled.rename(columns=rename_dict, inplace=True)
    
    if 'orig_bytes' in resampled.columns and 'resp_bytes' in resampled.columns:
        resampled['bidirectional_flow_ratio'] = resampled['orig_bytes'] / (resampled['resp_bytes'] + 1e-9)
        
    return resampled

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Chunk Zeek logs into sequential time-series windows.")
    parser.add_argument('--input', type=str, required=True, help="Path to prognos_features.log OR directory containing logs")
    parser.add_argument('--output', type=str, required=True, help="Path to save output CSV (e.g., sequences.csv)")
    parser.add_argument('--window', type=int, default=10, help="Window size in seconds (default 10)")
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    if input_path.is_dir():
        log_files = list(input_path.glob("*.log"))
        print(f"Found {len(log_files)} logs in directory.")
    else:
        log_files = [input_path]

    total_windows = 0
    first_write = True
    
    for f in log_files:
        try:
            if f.stat().st_size < 100:
                continue
                
            df = parse_zeek_log(f)
            
            if len(df) == 0:
                continue
                
            seq_df = create_time_series_sequences(df, window_seconds=args.window)
            
            # Stream directly to disk to prevent RAM explosion
            mode = 'w' if first_write else 'a'
            header = True if first_write else False
            seq_df.to_csv(args.output, mode=mode, header=header, index=False)
            
            first_write = False
            total_windows += len(seq_df)
            print(f"Processed {f.name} -> {len(seq_df)} windows")
            
        except Exception as e:
            print(f"Skipping corrupted log {f.name}: {e}")
            
    if total_windows == 0:
        print("Error: No valid sequences could be generated from the inputs.")
        exit(1)
        
    print(f"Saved massive dataset of {total_windows:,} sequence windows to {args.output}")