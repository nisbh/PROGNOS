import pandas as pd
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Downsample massive PROGNOS dataset for training.")
    parser.add_argument('--input', type=str, required=True)
    parser.add_argument('--output', type=str, required=True)
    parser.add_argument('--keep_normal_ratio', type=float, default=0.01)
    
    args = parser.parse_args()
    
    print(f"Streaming {args.input} to downsample Normal traffic...")
    
    chunksize = 2_000_000
    first_write = True
    total_attacks = 0
    total_normal = 0
    
    for chunk in pd.read_csv(args.input, chunksize=chunksize):
        # Keep ALL attacks
        attacks = chunk[chunk['mitre_label'] > 0]
        
        # Downsample Normal traffic
        normal = chunk[chunk['mitre_label'] == 0].sample(frac=args.keep_normal_ratio, random_state=42)
        
        # Combine
        balanced = pd.concat([attacks, normal]).sort_values('ts')
        
        total_attacks += len(attacks)
        total_normal += len(normal)
        
        mode = 'w' if first_write else 'a'
        header = True if first_write else False
        balanced.to_csv(args.output, mode=mode, header=header, index=False)
        first_write = False
        
    print(f"Finished! Kept {total_attacks:,} Attack windows and {total_normal:,} Normal windows.")
    print(f"Saved highly-optimized training dataset to: {args.output}")
