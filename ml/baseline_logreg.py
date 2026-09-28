import pickle
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix
from sklearn.model_selection import train_test_split

print("===========================================")
print(" PROGNOS V2 - LOGISTIC REGRESSION BASELINE ")
print("===========================================")

# 1. Load the balanced sequences
pkl_path = "data/balanced_sequences.pkl"
try:
    with open(pkl_path, 'rb') as f:
        data = pickle.load(f)
        
    X_list = []
    y_list = []
    for item in data:
        X_list.append(item[0]) # The Sequence (numpy array)
        y_list.append(item[1]) # The Label (int)
        
    X = np.array(X_list)
    y = np.array(y_list)
    
except Exception as e:
    print(f"Error loading data: {e}")
    exit()

print(f"[*] Loaded {len(X)} sequences.")

# 2. Flatten for Logistic Regression
X_flattened = X.reshape(X.shape[0], -1)
print(f"[*] Flattened shape for LogReg: {X_flattened.shape}")

# 3. Train/Test Split (80/20)
X_train, X_test, y_train, y_test = train_test_split(X_flattened, y, test_size=0.2, random_state=42)

# 4. Train Logistic Regression
print("[*] Training Logistic Regression model (this may take a moment)...")
clf = LogisticRegression(class_weight='balanced', max_iter=2000, n_jobs=-1, random_state=42)
clf.fit(X_train, y_train)

# 5. Evaluate
print("[*] Evaluating on Test Set...")
y_pred = clf.predict(X_test)

acc = accuracy_score(y_test, y_pred)
cm = confusion_matrix(y_test, y_pred)

print("\n--- Logistic Regression Baseline Results ---")
print(f"Overall Accuracy: {acc * 100:.2f}%\n")
print(classification_report(y_test, y_pred))
print("Confusion Matrix:")
print(cm)

# Extract Overall FPR
total_fp = cm.sum(axis=0) - np.diag(cm)
total_tn = cm.sum() - (cm.sum(axis=1) + cm.sum(axis=0) - np.diag(cm))
fpr = total_fp / (total_fp + total_tn)
overall_fpr = np.mean(fpr)
print(f"\nOverall False Positive Rate (FPR): {overall_fpr * 100:.2f}%")
