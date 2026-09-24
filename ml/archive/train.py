import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score, roc_auc_score, average_precision_score
from sklearn.preprocessing import label_binarize
from sklearn.utils.class_weight import compute_sample_weight
import joblib
import shap

def train_model(csv_path: str = "data/training_features_unsw.csv", model_out: str = "ml/model_unsw.pkl"):
    print(f"Loading training data from {csv_path}...")
    try:
        df = pd.read_csv(csv_path)
    except FileNotFoundError:
        print(f"Error: Could not find {csv_path}. Make sure to run replay_pacing.py to generate features first!")
        return

    # Drop timestamp (we don't train on the literal time)
    cols_to_drop = [col for col in df.columns if col.lower() == 'timestamp'] + ['label']
    X = df.drop(columns=cols_to_drop)
    y = df["label"]

    # Convert string labels to integers for XGBoost
    label_map = {"NORMAL": 0, "ELEVATED": 1, "NEAR-TERM": 2, "IMMINENT": 3}
    y_encoded = y.map(label_map)

    # Train/test split
    X_train, X_test, y_train, y_test = train_test_split(X, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded)

    print("Training XGBoost multi-class temporal forecasting model...")
    base_model = xgb.XGBClassifier(
        objective="multi:softprob",
        num_class=4,
        eval_metric="mlogloss",
        use_label_encoder=False,
        random_state=42,
        max_depth=8, # Deeper trees to learn complex temporal patterns
        n_estimators=200
    )

    print("Training XGBoost multi-class temporal forecasting model...")
    base_model.fit(X_train, y_train)

    print("Evaluating model...")
    y_pred = base_model.predict(X_test)
    y_prob = base_model.predict_proba(X_test)
    
    print(f"Accuracy: {accuracy_score(y_test, y_pred) * 100:.2f}%")
    
    # Calculate advanced metrics
    y_test_bin = label_binarize(y_test, classes=[0, 1, 2, 3])
    
    # ROC-AUC (One-vs-Rest)
    roc_auc = roc_auc_score(y_test_bin, y_prob, average='weighted', multi_class='ovr')
    print(f"ROC-AUC (Weighted OVR): {roc_auc:.4f}")
    
    # PR-AUC (Average Precision)
    pr_auc = average_precision_score(y_test_bin, y_prob, average='weighted')
    print(f"PR-AUC (Weighted): {pr_auc:.4f}")
    
    # Reverse map for classification report
    reverse_map = {v: k for k, v in label_map.items()}
    target_names = [reverse_map[i] for i in range(4)]
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, target_names=target_names))

    print(f"Saving model to {model_out}...")
    joblib.dump(base_model, model_out)
    
    # Save the label mapping as well for the inference script
    joblib.dump(reverse_map, "ml/label_map.pkl")
    
    # SHAP Explainability Demo
    print("\nCalculating SHAP values for explainability demo...")
    # SHAP doesn't support CalibratedClassifierCV directly well, so we train a quick 
    # secondary base model just to extract global feature importance for the presentation.
    explainer_model = xgb.XGBClassifier(objective="multi:softprob", num_class=4, random_state=42).fit(X_train, y_train)
    explainer = shap.TreeExplainer(explainer_model)
    shap_values = explainer.shap_values(X_test.iloc[:100]) # just a sample
    
    # In a real app we'd save this explainer or calculate it live.
    print("Model pipeline complete! Ready for PROGNOS forecasting.")

if __name__ == "__main__":
    train_model()
