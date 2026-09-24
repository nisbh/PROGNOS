import pandas as pd
import numpy as np
import torch
from torch.utils.data import Dataset, DataLoader
from sklearn.preprocessing import RobustScaler

class PrognosTrafficDataset(Dataset):
    """
    PyTorch Dataset for generating sliding windows of network traffic.
    Groups traffic by Source IP to maintain continuous individual temporal trajectories.
    """
    def __init__(self, csv_path, sequence_length=6, is_train=True, scaler=None):
        self.sequence_length = sequence_length
        self.is_train = is_train
        
        # Load the chunked Zeek sequences
        df = pd.read_csv(csv_path)
        
        # The features we want the model to learn from
        self.feature_cols = [
            'duration', 'orig_bytes', 'resp_bytes', 'orig_pkts', 'resp_pkts',
            'min_ttl_orig', 'max_ttl_orig', 'min_ttl_resp', 'max_ttl_resp',
            'avg_win_orig', 'avg_win_resp', 'payload_min_orig', 'payload_max_orig', 
            'payload_min_resp', 'payload_max_resp', 'frag_count', 'retrans_orig', 
            'retrans_resp', 'flag_syn', 'flag_ack', 'flag_fin', 'flag_rst', 
            'flag_psh', 'flag_urg', 'iat_mean', 'iat_max', 'iat_var',
            'flow_count', 'unique_dest_ports_scan_signature', 'bidirectional_flow_ratio'
        ]
        
        # Ensure all columns exist, fill missing with 0
        for col in self.feature_cols:
            if col not in df.columns:
                df[col] = 0.0
                
        # Fill NA/Inf
        df.replace([np.inf, -np.inf], np.nan, inplace=True)
        df.fillna(0, inplace=True)
        
        # Scaling
        if self.is_train:
            self.scaler = RobustScaler()
            df[self.feature_cols] = self.scaler.fit_transform(df[self.feature_cols])
        else:
            self.scaler = scaler
            df[self.feature_cols] = self.scaler.transform(df[self.feature_cols])
            
        # Group by Source IP and create rolling windows
        self.sequences = []
        self.labels = []
        
        # For now, we mock the labels (0: Normal, 1: Recon, 2: Initial Access, 3: Lateral, 4: C2)
        # In a real run, you would merge your ground-truth labels based on IP and Timestamp here.
        if 'mitre_label' not in df.columns:
            df['mitre_label'] = 0 # Default to normal
            
        if 'infiltration_prob' not in df.columns:
            df['infiltration_prob'] = 0.0

        for ip, group in df.groupby('id.orig_h'):
            # Must be sorted chronologically per IP
            group = group.sort_values('ts')
            features = group[self.feature_cols].values
            labels_mitre = group['mitre_label'].values
            labels_prob = group['infiltration_prob'].values
            
            # If the IP hasn't been active for enough windows, we can't create a sequence
            if len(features) < self.sequence_length:
                continue
                
            # Create sliding windows of size `sequence_length`
            for i in range(len(features) - self.sequence_length):
                seq_x = features[i : i + self.sequence_length]
                # The label is the state at the END of the sequence (or the next step)
                seq_y_mitre = labels_mitre[i + self.sequence_length]
                seq_y_prob = labels_prob[i + self.sequence_length]
                
                self.sequences.append(seq_x)
                self.labels.append((seq_y_mitre, seq_y_prob))

    def __len__(self):
        return len(self.sequences)

    def __getitem__(self, idx):
        x = torch.tensor(self.sequences[idx], dtype=torch.float32)
        y_mitre = torch.tensor(self.labels[idx][0], dtype=torch.long)
        y_prob = torch.tensor(self.labels[idx][1], dtype=torch.float32).unsqueeze(0)
        return x, y_mitre, y_prob

def get_dataloader(csv_path, batch_size=32, sequence_length=6, is_train=True, scaler=None):
    dataset = PrognosTrafficDataset(csv_path, sequence_length, is_train, scaler)
    dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=is_train, drop_last=True)
    return dataloader, dataset.scaler if is_train else None

if __name__ == "__main__":
    # Test dataset creation
    print("Testing dataset pipeline (requires sequences.csv)...")
    try:
        loader, scaler = get_dataloader("data/sequences.csv", batch_size=2)
        for batch_x, batch_y_mitre, batch_y_prob in loader:
            print(f"Batch X shape: {batch_x.shape}")
            print(f"Batch Y (MITRE) shape: {batch_y_mitre.shape}")
            print(f"Batch Y (Prob) shape: {batch_y_prob.shape}")
            break
        print("Dataset creation successful!")
    except Exception as e:
        print(f"Could not test dataset: {e}")
