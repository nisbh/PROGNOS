import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score, roc_auc_score, average_precision_score
from sklearn.preprocessing import label_binarize
import joblib

def train_fusion_model():
    print("Loading CIC-IDS2017 data...")
    try:
        cic_df = pd.read_csv("data/training_features.csv")
    except FileNotFoundError:
        print("Could not find data/training_features.csv")
        return
        
    print("Loading UNSW-NB15 data...")
    try:
        unsw_df = pd.read_csv("data/training_features_unsw.csv")
    except FileNotFoundError:
        print("Could not find data/training_features_unsw.csv")
        return

    # Drop any unique columns that shouldn't be trained on
    for df in [cic_df, unsw_df]:
        cols_to_drop = [col for col in df.columns if col.lower() in ['timestamp', 'attack_active']]
        if cols_to_drop:
            df.drop(columns=cols_to_drop, inplace=True)

    print("Fusing datasets...")
    # Concatenate and shuffle heavily to mix the distributions
    combined_df = pd.concat([cic_df, unsw_df], ignore_index=True)
    combined_df = combined_df.sample(frac=1, random_state=42).reset_index(drop=True)
    
    print(f"Total fused dataset size: {len(combined_df)}")
    print(combined_df['label'].value_counts())

    X = combined_df.drop(columns=["label"])
    y = combined_df["label"]

    label_map = {"NORMAL": 0, "ELEVATED": 1, "NEAR-TERM": 2, "IMMINENT": 3}
    y_encoded = y.map(label_map)

    # 80/20 train/test split (Stratified to maintain class distributions)
    X_train, X_test, y_train, y_test = train_test_split(X, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded)

    # To prevent overfitting, we'll extract a validation set from the training set
    # for XGBoost's early stopping
    X_train_sub, X_val, y_train_sub, y_val = train_test_split(X_train, y_train, test_size=0.1, random_state=42, stratify=y_train)

    print("Training XGBoost Fusion Model with Early Stopping (Anti-Overfitting)...")
    base_model = xgb.XGBClassifier(
        objective="multi:softprob",
        num_class=4,
        eval_metric="mlogloss",
        use_label_encoder=False,
        random_state=42,
        max_depth=9,
        learning_rate=0.19,
        min_child_weight=3,
        subsample=0.98,
        colsample_bytree=0.97,
        gamma=0.0045,
        n_estimators=611,
        early_stopping_rounds=20
    )

    base_model.fit(
        X_train_sub, y_train_sub,
        eval_set=[(X_val, y_val)],
        verbose=False
    )
    
    print(f"Best Iteration: {base_model.best_iteration}")

    print("\nEvaluating Master Model on Holdout Test Set...")
    y_pred = base_model.predict(X_test)
    y_prob = base_model.predict_proba(X_test)
    
    accuracy = accuracy_score(y_test, y_pred)
    print(f"Accuracy: {accuracy * 100:.2f}%")
    
    y_test_bin = label_binarize(y_test, classes=[0, 1, 2, 3])
    
    roc_auc = roc_auc_score(y_test_bin, y_prob, average='weighted', multi_class='ovr')
    print(f"ROC-AUC (Weighted OVR): {roc_auc:.4f}")
    
    pr_auc = average_precision_score(y_test_bin, y_prob, average='weighted')
    print(f"PR-AUC (Weighted): {pr_auc:.4f}")
    
    reverse_map = {v: k for k, v in label_map.items()}
    target_names = [reverse_map[i] for i in range(4)]
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, target_names=target_names))

    model_out = "ml/model_fusion.pkl"
    print(f"Saving Master Fusion model to {model_out}...")
    joblib.dump(base_model, model_out)
    
    # Do not overwrite the original model.pkl or label_map.pkl!
    print("Master Fusion Pipeline complete! The legacy models remain untouched.")

if __name__ == "__main__":
    train_fusion_model()
