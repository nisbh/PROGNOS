import pandas as pd
import argparse

def create_perfect_dataset(input_csv, output_csv, chunksize=2_000_000):
    print("Streaming data to create a perfectly balanced, ACTIVE dataset...")
    parts = []
    
    counts = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0}
    normal_budget = 15000  # Cap active Normal traffic to 15k rows to roughly match the sum of attacks
    
    for chunk in pd.read_csv(input_csv, chunksize=chunksize):
        if 'mitre_label' not in chunk.columns:
            break
            
        # FILTER OUT SILENT ROWS (The Silent Killer)
        active = chunk[(chunk.orig_bytes > 0) | (chunk.resp_bytes > 0) | (chunk.orig_pkts > 0)]
        
        # Keep all active attacks
        attacks = active[active.mitre_label != 0]
        if len(attacks) > 0:
            parts.append(attacks)
            for lbl in attacks.mitre_label.unique():
                counts[lbl] += len(attacks[attacks.mitre_label == lbl])
                
        # Downsample active Normal traffic
        normal = active[active.mitre_label == 0]
        if len(normal) > 0 and normal_budget > 0:
            take = min(len(normal), normal_budget)
            keep = normal.sample(n=take, random_state=42)
            parts.append(keep)
            counts[0] += len(keep)
            normal_budget -= len(keep)
            
    if parts:
        balanced = pd.concat(parts)
        if 'ts' in balanced.columns:
            balanced = balanced.sort_values('ts', kind='mergesort')
        balanced.to_csv(output_csv, index=False)
        print("Done!")
        print("Final Active Counts:", counts)

if __name__ == "__main__":
    create_perfect_dataset('data/master_2018_labeled.csv', 'data/perfect_train_2018.csv')
