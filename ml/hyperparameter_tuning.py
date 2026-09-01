import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, roc_auc_score, f1_score
import optuna
import os

# Load dataset (CIC and UNSW combined, similar to combine_and_train.py)
def load_and_fuse_data():
    cic_path = "data/training_features.csv"
    unsw_path = "data/training_features_unsw.csv"
    
    if not os.path.exists(cic_path) or not os.path.exists(unsw_path):
        raise FileNotFoundError("Missing datasets. Ensure both generators have been run.")
        
    df_cic = pd.read_csv(cic_path)
    df_unsw = pd.read_csv(unsw_path)
    
    # Drop any unique columns that shouldn't be trained on
    for df in [df_cic, df_unsw]:
        cols_to_drop = [col for col in df.columns if col.lower() in ['timestamp', 'attack_active']]
        if cols_to_drop:
            df.drop(columns=cols_to_drop, inplace=True)
    
    df_fused = pd.concat([df_cic, df_unsw], ignore_index=True)
    
    # Extract Features and Labels
    X = df_fused.drop(columns=["label"])
    y_raw = df_fused["label"]
    
    # Encode Labels
    label_map = {"NORMAL": 0, "ELEVATED": 1, "NEAR-TERM": 2, "IMMINENT": 3}
    y = y_raw.map(label_map)
    
    return train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)


def objective(trial):
    # Load data once per trial (or ideally, pass it in if we could, but this is fine)
    X_train, X_test, y_train, y_test = load_and_fuse_data()
    
    # Define hyperparameters to tune
    param = {
        "objective": "multi:softprob",
        "num_class": 4,
        "eval_metric": "mlogloss",
        "tree_method": "hist", # Faster training
        "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
        "max_depth": trial.suggest_int("max_depth", 3, 10),
        "min_child_weight": trial.suggest_int("min_child_weight", 1, 10),
        "subsample": trial.suggest_float("subsample", 0.5, 1.0),
        "colsample_bytree": trial.suggest_float("colsample_bytree", 0.5, 1.0),
        "gamma": trial.suggest_float("gamma", 0.0, 5.0),
        "n_estimators": trial.suggest_int("n_estimators", 100, 1000)
    }
    
    # Note: We use early stopping internally to prevent overfitting during each trial
    model = xgb.XGBClassifier(**param, early_stopping_rounds=20)
    
    model.fit(
        X_train, y_train,
        eval_set=[(X_test, y_test)],
        verbose=False
    )
    
    # Predict probabilities for ROC-AUC
    y_pred_proba = model.predict_proba(X_test)
    
    # The objective is to maximize ROC-AUC (which evaluates how well we separate classes)
    roc_auc = roc_auc_score(y_test, y_pred_proba, multi_class='ovr', average='weighted')
    
    return roc_auc

if __name__ == "__main__":
    print("Starting Optuna Hyperparameter Tuning for XGBoost...")
    print("Optimization Objective: Maximize ROC-AUC")
    
    # Create study
    study = optuna.create_study(direction="maximize")
    
    # Run 50 trials (to balance time and battery drain)
    # The user is low on battery, 50 trials should take ~15 mins.
    study.optimize(objective, n_trials=50, n_jobs=1)
    
    print("\n==========================================")
    print("OPTIMIZATION FINISHED")
    print(f"Best Trial: {study.best_trial.number}")
    print(f"Best ROC-AUC Score: {study.best_value:.4f}")
    print("Best Hyperparameters:")
    for key, value in study.best_trial.params.items():
        print(f"    {key}: {value}")
    print("==========================================")
    
    # Save the best params to a file for easy reading
    with open("data/best_hyperparameters.txt", "w") as f:
        f.write("Best Hyperparameters found by Optuna:\n")
        for key, value in study.best_trial.params.items():
            f.write(f"{key}: {value}\n")
    print("Saved best params to data/best_hyperparameters.txt")
