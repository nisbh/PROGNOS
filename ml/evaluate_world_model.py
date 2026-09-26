import torch
import argparse
import numpy as np
import pickle
import os
from sklearn.metrics import f1_score, precision_score, recall_score, classification_report
from dataset import get_dataloader
from world_model import PrognosWorldModel


def evaluate_model(
    weights_path,
    dataset_path,
    scaler_path="ml_scaler.pkl",
    batch_size=32,
    device="cuda" if torch.cuda.is_available() else "cpu"
):
    print(f"\n--- Loading PyTorch World Model on {device} ---")

    # ------------------------------------------------------------------
    # 1. Load the SAME RobustScaler that was fitted during training.
    #    Using a freshly-fitted scaler on test data would corrupt the
    #    feature values (data leakage + misaligned scaling parameters).
    # ------------------------------------------------------------------
    if os.path.exists(scaler_path):
        with open(scaler_path, "rb") as f:
            scaler = pickle.load(f)
        print(f"Loaded pre-fitted scaler from {scaler_path}")
        test_loader, _ = get_dataloader(
            dataset_path, batch_size=batch_size, sequence_length=6,
            is_train=False, scaler=scaler
        )
    else:
        # Fallback: fit a new scaler (acceptable if scaler.pkl doesn't exist yet)
        print(f"WARNING: {scaler_path} not found. Fitting a fresh scaler on test data.")
        print("         Re-run train_world_model.py to generate ml_scaler.pkl for correct evaluation.")
        test_loader, _ = get_dataloader(
            dataset_path, batch_size=batch_size, sequence_length=6, is_train=True
        )

    print(f"Loaded {len(test_loader.dataset):,} temporal sequences for evaluation.")

    # ------------------------------------------------------------------
    # 2. Initialise Model and Load Weights
    # ------------------------------------------------------------------
    model = PrognosWorldModel(input_features=30, num_classes=5).to(device)
    model.load_state_dict(torch.load(weights_path, map_location=device))
    model.eval()
    print("Model weights loaded successfully.")

    # ------------------------------------------------------------------
    # 3. Run Inference
    # ------------------------------------------------------------------
    print("\n--- Running AI Inference... ---")
    all_preds, all_labels = [], []

    with torch.no_grad():
        for x, y_mitre, _ in test_loader:
            x = x.to(device)
            mitre_logits, _, _ = model(x)
            preds = torch.argmax(mitre_logits, dim=1).cpu().numpy()
            all_preds.extend(preds)
            all_labels.extend(y_mitre.numpy())

    # ------------------------------------------------------------------
    # 4. Compute Metrics
    # ------------------------------------------------------------------
    all_preds  = np.array(all_preds)
    all_labels = np.array(all_labels)

    f1   = f1_score(all_labels, all_preds,        average='macro', zero_division=0)
    prec = precision_score(all_labels, all_preds, average='macro', zero_division=0)
    rec  = recall_score(all_labels, all_preds,    average='macro', zero_division=0)
    acc  = np.mean(all_preds == all_labels)

    print("\n============================================")
    print("      PROGNOS V2 EVALUATION METRICS       ")
    print("============================================")
    print(f"Accuracy:  {acc*100:.2f}%")
    print(f"Macro F1:  {f1:.4f}")
    print(f"Precision: {prec:.4f}")
    print(f"Recall:    {rec:.4f}")
    print("============================================")

    target_names  = ['Normal', 'Reconnaissance', 'Initial Access', 'Lateral Movement', 'C2']
    unique_labels = np.unique(all_labels)
    present_names = [target_names[i] for i in unique_labels if i < len(target_names)]

    print("\nDetailed MITRE ATT&CK Classification Report:")
    print(classification_report(
        all_labels, all_preds,
        labels=list(unique_labels),
        target_names=present_names,
        zero_division=0
    ))

    # ------------------------------------------------------------------
    # 5. Class-level breakdown for copy-paste into PPT
    # ------------------------------------------------------------------
    print("--- Per-Class Summary (copy into PPT) ---")
    from sklearn.metrics import precision_recall_fscore_support
    p, r, f, s = precision_recall_fscore_support(
        all_labels, all_preds, labels=list(unique_labels), zero_division=0
    )
    for i, cls in enumerate(unique_labels):
        if cls < len(target_names):
            print(f"  {target_names[cls]:<20}  P={p[i]:.2f}  R={r[i]:.2f}  F1={f[i]:.2f}  support={s[i]:,}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate PROGNOS CNN-LSTM World Model")
    parser.add_argument('--weights', type=str, default="world_model_weights.pt",
                        help="Path to trained .pt weights file")
    parser.add_argument('--dataset', type=str, default="data/train_ready_2018.csv",
                        help="Path to evaluation dataset CSV")
    parser.add_argument('--scaler',  type=str, default="ml_scaler.pkl",
                        help="Path to the pickled RobustScaler from training (default: ml_scaler.pkl)")
    args = parser.parse_args()

    try:
        evaluate_model(
            weights_path=args.weights,
            dataset_path=args.dataset,
            scaler_path=args.scaler
        )
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Make sure world_model_weights.pt and the dataset exist.")
