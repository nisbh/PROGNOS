import pandas as pd
import argparse

"""
PROGNOS Downsampler v2
=======================
Produces a balanced dataset for CNN-LSTM training.

Strategy:
  - Keep ALL rare attack classes (Recon, Lateral Movement)
  - Cap Normal traffic via --keep_normal_ratio (default 0.05)
  - Cap the bloated Initial Access class via --cap_initial_access
    (Initial Access has 680k rows; cap at 50k to prevent it from
     dominating the loss and making the model ignore rarer classes)

Usage:
  python ml/downsample.py \
      --input  data/master_2018_labeled.csv \
      --output data/train_ready_2018.csv \
      --keep_normal_ratio 0.05 \
      --cap_initial_access 50000
"""

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Downsample PROGNOS dataset for balanced CNN-LSTM training.")
    parser.add_argument('--input',  type=str, required=True,  help="Path to labeled master CSV")
    parser.add_argument('--output', type=str, required=True,  help="Path to write balanced CSV")
    parser.add_argument('--keep_normal_ratio',  type=float, default=0.05,
                        help="Fraction of Normal (class 0) rows to keep (default: 0.05 = 5%%)")
    parser.add_argument('--cap_initial_access', type=int, default=50000,
                        help="Maximum rows to keep for Initial Access (class 2) (default: 50000)")

    args = parser.parse_args()

    print(f"Streaming {args.input} for balanced downsampling...")
    print(f"  Keep Normal ratio     : {args.keep_normal_ratio*100:.1f}%")
    print(f"  Cap Initial Access at : {args.cap_initial_access:,} rows")

    chunksize = 2_000_000
    first_write = True

    # Accumulators per class
    label_names = {0: 'Normal', 1: 'Reconnaissance', 2: 'Initial Access',
                   3: 'Lateral Movement', 4: 'C2'}
    counts = {k: 0 for k in label_names}
    initial_access_budget = args.cap_initial_access  # rows remaining we can still write

    for chunk in pd.read_csv(args.input, chunksize=chunksize):

        if 'mitre_label' not in chunk.columns:
            print("ERROR: 'mitre_label' column missing. Run label_generator.py first.")
            break

        parts = []

        # Class 0 — Normal: random subsample
        normal = chunk[chunk['mitre_label'] == 0]
        if len(normal) > 0:
            keep = normal.sample(frac=args.keep_normal_ratio, random_state=42)
            parts.append(keep)
            counts[0] += len(keep)

        # Class 1 — Reconnaissance: keep ALL (only ~155 rows total)
        recon = chunk[chunk['mitre_label'] == 1]
        parts.append(recon)
        counts[1] += len(recon)

        # Class 2 — Initial Access: cap to budget
        ia = chunk[chunk['mitre_label'] == 2]
        if initial_access_budget > 0 and len(ia) > 0:
            take = min(len(ia), initial_access_budget)
            ia_keep = ia.sample(n=take, random_state=42) if take < len(ia) else ia
            parts.append(ia_keep)
            counts[2] += len(ia_keep)
            initial_access_budget -= len(ia_keep)

        # Class 3 — Lateral Movement: keep ALL (~3,276 rows)
        lat = chunk[chunk['mitre_label'] == 3]
        parts.append(lat)
        counts[3] += len(lat)

        # Class 4 — C2: keep ALL (~57,223 rows)
        c2 = chunk[chunk['mitre_label'] == 4]
        parts.append(c2)
        counts[4] += len(c2)

        if not parts:
            continue

        balanced = pd.concat(parts).sort_values('ts', kind='mergesort') \
                     if 'ts' in chunk.columns else pd.concat(parts)

        mode   = 'w' if first_write else 'a'
        header = first_write
        balanced.to_csv(args.output, mode=mode, header=header, index=False)
        first_write = False

    total = sum(counts.values())
    print("\n--- Final Balanced Class Distribution ---")
    for k, name in label_names.items():
        pct = (counts[k] / total * 100) if total > 0 else 0
        print(f"  [{k}] {name:<20} {counts[k]:>8,}  ({pct:.1f}%)")
    print(f"\n  TOTAL: {total:,} rows")
    print(f"\nSaved balanced training dataset to: {args.output}")
