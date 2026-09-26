import torch
import argparse
import numpy as np
from sklearn.metrics import f1_score, precision_score, recall_score, classification_report
from dataset import get_dataloader
from world_model import PrognosWorldModel

def evaluate_model(weights_path, dataset_path, batch_size=32, device="cuda" if torch.cuda.is_available() else "cpu"):
    print(f"\n--- Loading PyTorch World Model on {device} ---")
    
    # 1. Load Data (We use the entire dataset provided as the test set)
    test_loader, _ = get_dataloader(dataset_path, batch_size=batch_size, sequence_length=6, is_train=False)
    print(f"Loaded {len(test_loader.dataset)} unseen temporal sequences for testing.")
    
    # 2. Initialize Model and Load Weights
    model = PrognosWorldModel(input_features=30, num_classes=5).to(device)
    model.load_state_dict(torch.load(weights_path, map_location=device))
    model.eval()
    
    print("\n--- Running AI Inference... ---")
    all_preds = []
    all_labels = []
    
    with torch.no_grad():
        for x, y_mitre, _ in test_loader:
            x = x.to(device)
            mitre_logits, _, _ = model(x)
            preds = torch.argmax(mitre_logits, dim=1).cpu().numpy()
            all_preds.extend(preds)
            all_labels.extend(y_mitre.numpy())
            
    # 3. Calculate Metrics
    f1 = f1_score(all_labels, all_preds, average='macro', zero_division=0)
    prec = precision_score(all_labels, all_preds, average='macro', zero_division=0)
    rec = recall_score(all_labels, all_preds, average='macro', zero_division=0)
    acc = np.mean(np.array(all_preds) == np.array(all_labels))
    
    print("\n============================================")
    print("      PROGNOS V2 EVALUATION METRICS       ")
    print("============================================")
    print(f"Accuracy:  {acc*100:.2f}%")
    print(f"Macro F1:  {f1:.4f}")
    print(f"Precision: {prec:.4f}")
    print(f"Recall:    {rec:.4f}")
    print("============================================")
    
    print("\nDetailed MITRE ATT&CK Classification Report:")
    target_names = ['Normal', 'Reconnaissance', 'Initial Access', 'Lateral Movement', 'C2']
    # Filter target names to only those present in the labels to avoid sklearn warnings
    unique_labels = np.unique(all_labels)
    present_names = [target_names[i] for i in unique_labels]
    print(classification_report(all_labels, all_preds, target_names=present_names, zero_division=0))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate PyTorch CNN-LSTM World Model")
    parser.add_argument('--weights', type=str, default="world_model_weights.pt", help="Path to trained .pt file")
    parser.add_argument('--dataset', type=str, default="data/train_ready_2018.csv", help="Path to test dataset")
    args = parser.parse_args()
    
    try:
        evaluate_model(weights_path=args.weights, dataset_path=args.dataset)
    except FileNotFoundError as e:
        print(f"Error: {e}")
