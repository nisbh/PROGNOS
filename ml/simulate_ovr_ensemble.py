import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score

def load_data():
    cic_df = pd.read_csv("data/training_features.csv")
    unsw_df = pd.read_csv("data/training_features_unsw.csv")
    
    for df in [cic_df, unsw_df]:
        cols_to_drop = [col for col in df.columns if col.lower() in ['timestamp', 'attack_active']]
        if cols_to_drop:
            df.drop(columns=cols_to_drop, inplace=True)

    combined_df = pd.concat([cic_df, unsw_df], ignore_index=True)
    combined_df = combined_df.sample(frac=1, random_state=42).reset_index(drop=True)
    return combined_df

def train_and_evaluate_ensemble():
    print("Loading fused datasets...")
    df = load_data()
    
    X = df.drop(columns=["label"])
    y_raw = df["label"]
    
    X_train, X_test, y_train_raw, y_test_raw = train_test_split(
        X, y_raw, test_size=0.2, random_state=42, stratify=y_raw
    )
    
    # We will train 3 binary classifiers
    targets = ["ELEVATED", "NEAR-TERM", "IMMINENT"]
    models = {}
    
    for target in targets:
        print(f"\nTraining binary model for: {target}")
        
        # 1 if target, 0 if anything else
        y_train_binary = (y_train_raw == target).astype(int)
        y_test_binary = (y_test_raw == target).astype(int)
        
        # Split a validation set for early stopping
        X_train_sub, X_val, y_train_sub, y_val = train_test_split(
            X_train, y_train_binary, test_size=0.1, random_state=42, stratify=y_train_binary
        )
        
        model = xgb.XGBClassifier(
            objective="binary:logistic",
            eval_metric="logloss",
            use_label_encoder=False,
            random_state=42,
            max_depth=9,
            learning_rate=0.19,
            min_child_weight=3,
            subsample=0.98,
            colsample_bytree=0.97,
            gamma=0.0045,
            n_estimators=600,
            early_stopping_rounds=20
        )
        
        model.fit(
            X_train_sub, y_train_sub,
            eval_set=[(X_val, y_val)],
            verbose=False
        )
        
        models[target] = model
        print(f"[{target}] Best Iteration: {model.best_iteration}")

    print("\n--- Evaluating Ensemble on Test Set ---")
    
    # Get probabilities from all 3 models for the test set
    prob_elevated = models["ELEVATED"].predict_proba(X_test)[:, 1]
    prob_nearterm = models["NEAR-TERM"].predict_proba(X_test)[:, 1]
    prob_imminent = models["IMMINENT"].predict_proba(X_test)[:, 1]
    
    # Combine predictions
    # If the max probability across the 3 models is < 0.5, we classify as NORMAL
    # Otherwise, we classify as whichever model has the highest confidence
    
    y_pred_final = []
    
    for i in range(len(X_test)):
        probs = {
            "ELEVATED": prob_elevated[i],
            "NEAR-TERM": prob_nearterm[i],
            "IMMINENT": prob_imminent[i]
        }
        
        max_target = max(probs, key=probs.get)
        max_prob = probs[max_target]
        
        if max_prob < 0.5:
            y_pred_final.append("NORMAL")
        else:
            y_pred_final.append(max_target)
            
    # Calculate final accuracy against true raw labels
    accuracy = accuracy_score(y_test_raw, y_pred_final)
    print(f"\nEnsemble Accuracy: {accuracy * 100:.2f}%")
    
    print("\nClassification Report:")
    print(classification_report(y_test_raw, y_pred_final))

if __name__ == "__main__":
    train_and_evaluate_ensemble()
