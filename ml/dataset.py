import torch
from torch.utils.data import Dataset, DataLoader
import pickle

class PrognosTrafficDataset(Dataset):
    def __init__(self, pkl_path):
        with open(pkl_path, 'rb') as f:
            self.sequences = pickle.load(f)

    def __len__(self):
        return len(self.sequences)

    def __getitem__(self, idx):
        x_np, y_mitre_np, y_prob_np = self.sequences[idx]
        x = torch.tensor(x_np, dtype=torch.float32)
        y_mitre = torch.tensor(y_mitre_np, dtype=torch.long)
        y_prob = torch.tensor(y_prob_np, dtype=torch.float32).unsqueeze(0)
        return x, y_mitre, y_prob

def get_dataloader(pkl_path, batch_size=32, is_train=True):
    dataset = PrognosTrafficDataset(pkl_path)
    dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=is_train, drop_last=True)
    return dataloader, None # Scaler is already applied globally
