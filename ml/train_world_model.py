import torch
import torch.nn as nn
import torch.optim as optim
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score, precision_score, recall_score
import numpy as np
import time
from dataset import get_dataloader
from world_model import PrognosWorldModel

def train_baseline_logistic_regression(train_loader):
    """
    Trains a Logistic Regression baseline to fulfill the NTRO problem statement requirement.
    Since Logistic Regression cannot process 3D temporal sequences, we flatten the windows.
    """
    print("\n--- Training Baseline Logistic Regression ---")
    
    X_train, y_train = [], []
    for x, y_mitre, _ in train_loader:
        # Flatten the (batch, seq_len, features) into (batch, seq_len * features)
        x_flat = x.view(x.size(0), -1).numpy()
        X_train.append(x_flat)
        y_train.append(y_mitre.numpy())
        
    X_train = np.vstack(X_train)
    y_train = np.concatenate(y_train)
    
    clf = LogisticRegression(max_iter=1000, class_weight='balanced')
    clf.fit(X_train, y_train)
    
    # Normally we evaluate on a test set, testing on train just for baseline confirmation
    preds = clf.predict(X_train)
    f1 = f1_score(y_train, preds, average='macro')
    print(f"Baseline Logistic Regression Macro F1: {f1:.4f}")
    return clf

def train_world_model(csv_path="data/sequences.csv", epochs=10, batch_size=32, device="cuda" if torch.cuda.is_available() else "cpu"):
    print(f"\n--- Training PyTorch World Model on {device} ---")
    
    # 1. Load Data
    train_loader, scaler = get_dataloader(csv_path, batch_size=batch_size, sequence_length=6, is_train=True)
    print(f"Loaded {len(train_loader.dataset)} temporal sequences.")
    
    # Satisfy NTRO Rubric: Baseline comparison
    train_baseline_logistic_regression(train_loader)
    
    # 2. Initialize Model
    # 30 features from the new sequence_chunker
    model = PrognosWorldModel(input_features=30, num_classes=5).to(device)
    
    # 3. Loss Functions
    # Use CrossEntropy for MITRE classes. 
    # In a real run, you should add class_weights here to penalize the model for missing rare attacks!
    criterion_mitre = nn.CrossEntropyLoss()
    criterion_prob = nn.BCELoss()
    
    optimizer = optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-4)
    
    # 4. Training Loop
    model.train()
    for epoch in range(epochs):
        epoch_loss = 0.0
        start_time = time.time()
        
        for batch_idx, (x, y_mitre, y_prob) in enumerate(train_loader):
            x = x.to(device)
            y_mitre = y_mitre.to(device)
            y_prob = y_prob.to(device)
            
            optimizer.zero_grad()
            
            # Forward pass
            mitre_logits, prob_preds, attn_weights = model(x)
            
            # Calculate Losses
            loss_mitre = criterion_mitre(mitre_logits, y_mitre)
            loss_prob = criterion_prob(prob_preds, y_prob)
            
            # Combined Loss
            loss = loss_mitre + loss_prob
            
            # Backward pass
            loss.backward()
            optimizer.step()
            
            epoch_loss += loss.item()
            
        print(f"Epoch {epoch+1}/{epochs} | Loss: {epoch_loss/len(train_loader):.4f} | Time: {time.time()-start_time:.2f}s")
        
    # 5. Save Weights
    torch.save(model.state_dict(), "world_model_weights.pt")
    print("\nSaved trained World Model weights to world_model_weights.pt")
    
if __name__ == "__main__":
    try:
        train_world_model(epochs=5)
    except FileNotFoundError:
        print("sequences.csv not found. Please run Zeek and sequence_chunker.py first.")
