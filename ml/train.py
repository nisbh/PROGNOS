import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import classification_report, accuracy_score
import joblib
import shap

def train_model(csv_path: str = "data/training_features.csv", model_out: str = "ml/model.pkl"):
    print(f"Loading training data from {csv_path}...")
    try:
        df = pd.read_csv(csv_path)
    except FileNotFoundError:
        print(f"Error: Could not find {csv_path}. Make sure to run replay_pacing.py to generate features first!")
        return

    # Drop timestamp (we don't train on the literal time)
    X = df.drop(columns=["timestamp", "label"])
    y = df["label"]

    # Convert string labels to integers for XGBoost
    label_map = {"NORMAL": 0, "ELEVATED": 1, "NEAR-TERM": 2, "IMMINENT": 3}
    y_encoded = y.map(label_map)

    # Train/test split
    X_train, X_test, y_train, y_test = train_test_split(X, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded)

    print("Training XGBoost base classifier...")
    # Initialize base XGBoost model
    # We use multi:softprob for multiclass probabilities
    base_model = xgb.XGBClassifier(
        objective="multi:softprob",
        num_class=4,
        eval_metric="mlogloss",
        use_label_encoder=False,
        random_state=42
    )

    # Calibrate probabilities so that the dashboard displays smooth, realistic percentages
    # rather than just binary step functions.
    print("Calibrating probabilities...")
    calibrated_model = CalibratedClassifierCV(base_model, method='sigmoid', cv=3)
    calibrated_model.fit(X_train, y_train)

    print("Evaluating model...")
    y_pred = calibrated_model.predict(X_test)
    print(f"Accuracy: {accuracy_score(y_test, y_pred) * 100:.2f}%")
    
    # Reverse map for classification report
    reverse_map = {v: k for k, v in label_map.items()}
    target_names = [reverse_map[i] for i in range(4)]
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, target_names=target_names))

    print(f"Saving calibrated model to {model_out}...")
    joblib.dump(calibrated_model, model_out)
    
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
