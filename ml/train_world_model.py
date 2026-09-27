import torch
import torch.nn as nn
import torch.optim as optim
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score, precision_score, recall_score, classification_report
from sklearn.utils.class_weight import compute_class_weight
import numpy as np
import time
import pickle
import os
from dataset import get_dataloader
from world_model import PrognosWorldModel
import argparse
from torch.utils.data import random_split, DataLoader, Subset
import torch.nn.functional as F

class FocalLoss(nn.Module):
    def __init__(self, weight=None, gamma=2.0, reduction='mean'):
        super(FocalLoss, self).__init__()
        self.weight = weight
        self.gamma = gamma
        self.reduction = reduction

    def forward(self, inputs, targets):
        ce_loss = F.cross_entropy(inputs, targets, weight=self.weight, reduction='none')
        pt = torch.exp(-ce_loss)
        focal_loss = ((1 - pt) ** self.gamma) * ce_loss
        if self.reduction == 'mean':
            return focal_loss.mean()
        elif self.reduction == 'sum':
            return focal_loss.sum()
        else:
            return focal_loss



def train_baseline_logistic_regression(train_loader):
    """
    Trains a Logistic Regression baseline to fulfill the NTRO problem statement requirement.
    Since Logistic Regression cannot process 3D temporal sequences, we flatten the windows.
    """
    print("\n--- Training Baseline Logistic Regression ---")

    X_train, y_train = [], []
    for x, y_mitre, _ in train_loader:
        x_flat = x.view(x.size(0), -1).numpy()
        X_train.append(x_flat)
        y_train.append(y_mitre.numpy())

    X_train = np.vstack(X_train)
    y_train = np.concatenate(y_train)

    clf = LogisticRegression(max_iter=1000, class_weight='balanced')

    if len(np.unique(y_train)) < 2:
        print("Warning: Only one class found. Skipping Logistic Regression baseline.")
        return None

    clf.fit(X_train, y_train)
    preds = clf.predict(X_train)
    f1 = f1_score(y_train, preds, average='macro', zero_division=0)
    print(f"Baseline Logistic Regression Macro F1 (train): {f1:.4f}")
    return clf


def evaluate_pytorch_model(model, test_loader, device):
    """Evaluates the PyTorch World Model on the unseen test set."""
    model.eval()
    all_preds, all_labels = [], []

    with torch.no_grad():
        for x, y_mitre, _ in test_loader:
            x = x.to(device)
            mitre_logits, _, _ = model(x)
            preds = torch.argmax(mitre_logits, dim=1).cpu().numpy()
            all_preds.extend(preds)
            all_labels.extend(y_mitre.numpy())

    f1   = f1_score(all_labels, all_preds,        average='macro', zero_division=0)
    prec = precision_score(all_labels, all_preds, average='macro', zero_division=0)
    rec  = recall_score(all_labels, all_preds,    average='macro', zero_division=0)
    acc  = np.mean(np.array(all_preds) == np.array(all_labels))

    print("\n============================================")
    print("   PROGNOS V2 TEST-SET EVALUATION METRICS  ")
    print("============================================")
    print(f"Accuracy:  {acc*100:.2f}%")
    print(f"Macro F1:  {f1:.4f}")
    print(f"Precision: {prec:.4f}")
    print(f"Recall:    {rec:.4f}")
    print("============================================")

    target_names = ['Normal', 'Reconnaissance', 'Initial Access', 'Lateral Movement', 'C2']
    unique_labels = np.unique(all_labels)
    present_names = [target_names[i] for i in unique_labels if i < len(target_names)]
    print("\nDetailed MITRE ATT&CK Classification Report:")
    print(classification_report(all_labels, all_preds,
                                labels=list(unique_labels),
                                target_names=present_names,
                                zero_division=0))
    return f1


def train_world_model(
    csv_path="data/balanced_sequences.pkl",
    epochs=10,
    batch_size=32,
    device="cuda" if torch.cuda.is_available() else "cpu"
):
    print(f"\n--- Training PyTorch World Model on {device} ---")

    # -----------------------------------------------------------------------
    # 1. Load Data + persist the RobustScaler for use at inference/eval time
    # -----------------------------------------------------------------------
    full_loader, _ = get_dataloader(
        csv_path, batch_size=batch_size, is_train=True
    )
    full_dataset = full_loader.dataset

    print(f"Dataset loaded from {csv_path}")

    # -----------------------------------------------------------------------
    # 2. 80/20 Train-Test Split
    # -----------------------------------------------------------------------
    train_size = int(0.8 * len(full_dataset))
    test_size  = len(full_dataset) - train_size
    
    # Now that sequences are non-overlapping, we can safely use random_split!
    train_dataset, test_dataset = random_split(full_dataset, [train_size, test_size])

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True,  drop_last=True)
    test_loader  = DataLoader(test_dataset,  batch_size=batch_size, shuffle=False, drop_last=True)

    print(f"Total sequences : {len(full_dataset):,}")
    print(f"Train (80%)     : {train_size:,}")
    print(f"Test  (20%)     : {test_size:,}")

    # -----------------------------------------------------------------------
    # 3. Class Weights — the critical fix for imbalanced MITRE labels
    # -----------------------------------------------------------------------
    all_labels_np = np.array([full_dataset[i][1].item() for i in range(len(full_dataset))])
    unique_classes = np.unique(all_labels_np)

    cw = compute_class_weight(class_weight='balanced', classes=unique_classes, y=all_labels_np)
    # Build a weight tensor of size num_classes (5); classes absent in data get weight=1.0
    class_weights_tensor = torch.ones(5, dtype=torch.float32)
    for cls, w in zip(unique_classes, cw):
        class_weights_tensor[int(cls)] = w
    class_weights_tensor = class_weights_tensor.to(device)

    print("\nClass weights applied to CrossEntropyLoss:")
    names = ['Normal', 'Recon', 'Initial Access', 'Lateral', 'C2']
    for i, (n, w) in enumerate(zip(names, class_weights_tensor.cpu().tolist())):
        print(f"  [{i}] {n:<18} weight = {w:.4f}")

    # -----------------------------------------------------------------------
    # 4. NTRO Rubric: Baseline comparison
    # -----------------------------------------------------------------------
    train_baseline_logistic_regression(train_loader)

    # -----------------------------------------------------------------------
    # 5. Initialise Model + Loss + Optimiser
    # -----------------------------------------------------------------------
    model = PrognosWorldModel(input_features=30, num_classes=5).to(device)

    # Simple CrossEntropyLoss without extreme class weights
    criterion_mitre = nn.CrossEntropyLoss()
    criterion_prob  = nn.BCELoss()

    optimizer = optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-4)

    # Learning-rate scheduler: cosine annealing for smoother convergence
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)

    # -----------------------------------------------------------------------
    # 6. Training Loop
    # -----------------------------------------------------------------------
    print(f"\n--- Starting Training ({epochs} epochs) ---")
    best_f1 = 0.0
    
    for epoch in range(epochs):
        model.train()
        epoch_loss_mitre = 0.0
        epoch_loss_prob  = 0.0
        start_time = time.time()

        for x, y_mitre, y_prob in train_loader:
            x       = x.to(device)
            y_mitre = y_mitre.to(device)
            y_prob  = y_prob.to(device)

            optimizer.zero_grad()

            mitre_logits, prob_preds, _ = model(x)

            loss_mitre = criterion_mitre(mitre_logits, y_mitre)
            loss_prob  = criterion_prob(prob_preds, y_prob)
            
            # The model should just focus on predicting the correct attack
            loss       = loss_mitre

            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=5.0)  # loosened stability for Focal Loss
            optimizer.step()

            epoch_loss_mitre += loss_mitre.item()
            epoch_loss_prob  += loss_prob.item()

        scheduler.step()

        elapsed = time.time() - start_time
        print(
            f"Epoch {epoch+1:02d}/{epochs} | "
            f"MITRE Loss: {epoch_loss_mitre/len(train_loader):.4f} | "
            f"Prob Loss: {epoch_loss_prob/len(train_loader):.4f} | "
            f"LR: {scheduler.get_last_lr()[0]:.5f} | "
            f"Time: {elapsed:.1f}s"
        )
        
        # Validation and Best Checkpointing
        val_f1 = evaluate_pytorch_model(model, test_loader, device)
        if val_f1 > best_f1:
            best_f1 = val_f1
            torch.save(model.state_dict(), "world_model_weights_best.pt")
            print(f"*** New BEST model saved with F1: {best_f1:.4f} ***")
            
    # -----------------------------------------------------------------------
    # 7. Final Evaluation on Held-Out Test Set (Using Best Weights)
    # -----------------------------------------------------------------------
    print("\nLoading best weights for final evaluation...")
    model.load_state_dict(torch.load("world_model_weights_best.pt"))
    evaluate_pytorch_model(model, test_loader, device)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train PyTorch CNN-LSTM World Model")
    parser.add_argument('--dataset', type=str, default="data/balanced_sequences.pkl",
                        help="Path to balanced training dataset")
    parser.add_argument('--epochs', type=int, default=10,
                        help="Number of training epochs (default: 10)")
    args = parser.parse_args()

    try:
        train_world_model(csv_path=args.dataset, epochs=args.epochs)
    except FileNotFoundError:
        print(f"Error: {args.dataset} not found. Run label_generator.py and downsample.py first.")
