import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.svm import SVC
from sklearn.neighbors import KNeighborsClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import GaussianNB
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score
import time

def run_experiments():
    print("Loading and Fusing Datasets for Experiment...")
    cic_df = pd.read_csv("data/training_features.csv")
    unsw_df = pd.read_csv("data/training_features_unsw.csv")

    for df in [cic_df, unsw_df]:
        cols_to_drop = [col for col in df.columns if col.lower() in ['timestamp', 'attack_active']]
        if cols_to_drop:
            df.drop(columns=cols_to_drop, inplace=True)

    combined = pd.concat([cic_df, unsw_df], ignore_index=True)
    combined = combined.sample(frac=1, random_state=42).reset_index(drop=True)
    
    X = combined.drop(columns=["label"])
    y = combined["label"].map({"NORMAL": 0, "ELEVATED": 1, "NEAR-TERM": 2, "IMMINENT": 3})

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    results = {}

    # 1. Random Forest
    print("\n--- Training Random Forest ---")
    start = time.time()
    rf = RandomForestClassifier(n_estimators=200, max_depth=15, random_state=42, n_jobs=-1)
    rf.fit(X_train, y_train)
    rf_pred = rf.predict(X_test)
    rf_acc = accuracy_score(y_test, rf_pred)
    rf_time = time.time() - start
    print(f"Random Forest Accuracy: {rf_acc*100:.2f}% (Time: {rf_time:.2f}s)")
    results["Random Forest"] = {"Accuracy": rf_acc, "Time": rf_time}

    # 2. Deep Learning (MLP Neural Network)
    print("\n--- Training Deep Learning (MLP) ---")
    start = time.time()
    mlp = MLPClassifier(hidden_layer_sizes=(64, 32), max_iter=500, random_state=42, early_stopping=True)
    mlp.fit(X_train, y_train)
    mlp_acc = accuracy_score(y_test, mlp.predict(X_test))
    results["Deep Learning (MLP)"] = {"Accuracy": mlp_acc, "Time": time.time() - start}
    
    # 3. Support Vector Machine (SVM)
    print("--- Training SVM ---")
    start = time.time()
    svm = SVC(kernel='rbf', random_state=42, max_iter=2000)
    svm.fit(X_train, y_train)
    svm_acc = accuracy_score(y_test, svm.predict(X_test))
    results["SVM (RBF)"] = {"Accuracy": svm_acc, "Time": time.time() - start}

    # 4. K-Nearest Neighbors (KNN)
    print("--- Training KNN ---")
    start = time.time()
    knn = KNeighborsClassifier(n_neighbors=5, n_jobs=-1)
    knn.fit(X_train, y_train)
    knn_acc = accuracy_score(y_test, knn.predict(X_test))
    results["K-Nearest Neighbors"] = {"Accuracy": knn_acc, "Time": time.time() - start}

    # 5. Logistic Regression
    print("--- Training Logistic Regression ---")
    start = time.time()
    lr = LogisticRegression(max_iter=1000, random_state=42, n_jobs=-1)
    lr.fit(X_train, y_train)
    lr_acc = accuracy_score(y_test, lr.predict(X_test))
    results["Logistic Regression"] = {"Accuracy": lr_acc, "Time": time.time() - start}

    # 6. Naive Bayes
    print("--- Training Naive Bayes ---")
    start = time.time()
    nb = GaussianNB()
    nb.fit(X_train, y_train)
    nb_acc = accuracy_score(y_test, nb.predict(X_test))
    results["Naive Bayes"] = {"Accuracy": nb_acc, "Time": time.time() - start}

    # 7. Decision Tree
    print("--- Training Decision Tree ---")
    start = time.time()
    dt = DecisionTreeClassifier(random_state=42)
    dt.fit(X_train, y_train)
    dt_acc = accuracy_score(y_test, dt.predict(X_test))
    results["Decision Tree"] = {"Accuracy": dt_acc, "Time": time.time() - start}

    # 8. XGBoost (For comparison reference)
    import xgboost as xgb
    print("\n--- Training XGBoost (Our Current Master Model) ---")
    start = time.time()
    xgb_model = xgb.XGBClassifier(objective="multi:softprob", num_class=4, eval_metric="mlogloss", 
                                  random_state=42, max_depth=10, learning_rate=0.05, n_estimators=500)
    xgb_model.fit(X_train, y_train)
    xgb_pred = xgb_model.predict(X_test)
    xgb_acc = accuracy_score(y_test, xgb_pred)
    xgb_time = time.time() - start
    print(f"XGBoost Accuracy: {xgb_acc*100:.2f}% (Time: {xgb_time:.2f}s)")
    results["XGBoost"] = {"Accuracy": xgb_acc, "Time": xgb_time}

    print("\n=== EXPERIMENT SUMMARY ===")
    for model, data in results.items():
        print(f"{model}: {data['Accuracy']*100:.2f}% Accuracy | {data['Time']:.2f}s Training Time")

if __name__ == "__main__":
    run_experiments()
