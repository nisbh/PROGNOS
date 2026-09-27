import pandas as pd
import numpy as np
import torch
from sklearn.preprocessing import RobustScaler
import pickle
import argparse

def generate_sequences(input_csv="data/master_2018_labeled.csv", output_file="data/balanced_sequences.pkl"):
    print("Streaming 20GB dataset to generate PERFECT sequences...")
    
    feature_cols = [
        'duration', 'orig_bytes', 'resp_bytes', 'orig_pkts', 'resp_pkts',
        'min_ttl_orig', 'max_ttl_orig', 'min_ttl_resp', 'max_ttl_resp',
        'avg_win_orig', 'avg_win_resp', 'payload_min_orig', 'payload_max_orig', 
        'payload_min_resp', 'payload_max_resp', 'frag_count', 'retrans_orig', 
        'retrans_resp', 'flag_syn', 'flag_ack', 'flag_fin', 'flag_rst', 
        'flag_psh', 'flag_urg', 'iat_mean', 'iat_max', 'iat_var',
        'flow_count', 'unique_dest_ports_scan_signature', 'bidirectional_flow_ratio'
    ]
    
    chunksize = 2_000_000
    sequence_length = 6
    
    all_normal_seqs = []
    all_attack_seqs = []
    
    scaler = RobustScaler()
    scaler_partial_fits = 0
    
    for chunk in pd.read_csv(input_csv, chunksize=chunksize):
        if 'mitre_label' not in chunk.columns:
            break
            
        # 1. Filter out absolute silence
        active = chunk[(chunk.orig_bytes > 0) | (chunk.resp_bytes > 0) | (chunk.orig_pkts > 0)].copy()
        if active.empty:
            continue
            
        # Fill NA
        active.replace([np.inf, -np.inf], np.nan, inplace=True)
        active.fillna(0, inplace=True)
        
        # We need to scale BEFORE sequence creation so the model sees normalized data
        # To avoid memory explosion, we fit the scaler incrementally if possible, 
        # but RobustScaler doesn't support partial_fit. 
        # Instead, we will scale AFTER we collect all balanced sequences.
        
        # 2. Group by IP to ensure sequences belong to the same computer!
        for ip, group in active.groupby('id.orig_h'):
            group = group.sort_values('ts')
            features = group[feature_cols].values
            labels_mitre = group['mitre_label'].values
            labels_prob = group['infiltration_prob'].values
            
            if len(features) >= sequence_length:
                # Non-overlapping stride
                for i in range(0, len(features) - sequence_length + 1, sequence_length):
                    seq_x = features[i : i + sequence_length]
                    seq_y_mitre = labels_mitre[i + sequence_length - 1]
                    seq_y_prob = labels_prob[i + sequence_length - 1]
                    
                    if seq_y_mitre == 0:
                        all_normal_seqs.append((seq_x, seq_y_mitre, seq_y_prob))
                    else:
                        all_attack_seqs.append((seq_x, seq_y_mitre, seq_y_prob))
                        
    print(f"Total Attack Sequences Generated: {len(all_attack_seqs)}")
    print(f"Total Normal Sequences Generated: {len(all_normal_seqs)}")
    
    # 3. Balance the sequences
    # Keep all attacks, and take a random sample of Normal sequences equal to the attack count
    import random
    random.seed(42)
    
    if len(all_attack_seqs) > 0:
        target_normal_count = min(len(all_normal_seqs), max(len(all_attack_seqs) * 2, 5000)) # Ensure at least some normal
    else:
        target_normal_count = min(len(all_normal_seqs), 5000)
        
    sampled_normal_seqs = random.sample(all_normal_seqs, target_normal_count)
    
    final_sequences = sampled_normal_seqs + all_attack_seqs
    random.shuffle(final_sequences)
    
    print(f"Final Balanced Dataset: {len(final_sequences)} sequences.")
    
    # 4. Scale the features globally now that we have a tiny balanced subset
    X_all = np.vstack([seq[0] for seq in final_sequences]) # shape: (N*6, 30)
    scaler.fit(X_all)
    
    scaled_sequences = []
    for seq_x, seq_y_mitre, seq_y_prob in final_sequences:
        scaled_x = scaler.transform(seq_x)
        scaled_sequences.append((scaled_x, seq_y_mitre, seq_y_prob))
        
    # Save the scaler so train_world_model.py doesn't overwrite it
    with open("ml_scaler.pkl", "wb") as f:
        pickle.dump(scaler, f)
        
    with open(output_file, "wb") as f:
        pickle.dump(scaled_sequences, f)
        
    print(f"Saved balanced sequences to {output_file}")
    
if __name__ == "__main__":
    generate_sequences()
