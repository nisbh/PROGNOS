import joblib
import pandas as pd
import shap

MODEL = joblib.load("ml/model_fusion.pkl")
EXPLAINER = shap.TreeExplainer(MODEL)

FEATURE_NAMES = [
    "connections_per_sec", "syn_rate", "avg_packet_size", "flow_duration_mean",
    "fwd_packets_sum", "bwd_packets_sum", "flow_packets_s_mean",
    "connections_per_sec_diff", "syn_rate_diff", "connections_1m_avg",
    "syn_rate_1m_avg", "packet_size_1m_avg"
]
df = pd.DataFrame([[10, 0.1, 200, 5, 100, 50, 500, 1, 0, 10, 0.1, 190]], columns=FEATURE_NAMES)

shap_values = EXPLAINER.shap_values(df)
print(type(shap_values))
if isinstance(shap_values, list):
    print(f"List of length: {len(shap_values)}")
    print(f"Shape of first item: {shap_values[0].shape}")
else:
    print(f"Array shape: {shap_values.shape}")
