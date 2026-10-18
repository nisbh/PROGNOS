# PROGNOS v2

**Predictive State-Transition Forecasting for Security Operations Centers**

PROGNOS is a proactive network intrusion forecasting system built for the Smart India Hackathon 2026. It answers a deceptively simple question that traditional security tools cannot: *what is this attacker about to do next?*

Standard Network Intrusion Detection Systems (NIDS) and SIEMs operate reactively. They trigger an alert after an attack has already been executed, after the SYN flood has crashed the server, after the brute-force credentials have been accepted. PROGNOS shifts that window backward. By analyzing the temporal trajectory of network behavior, it identifies and classifies attackers during their early reconnaissance and initial access phases, before any payload is delivered.

---

## How It Works

Modern cyberattacks are not instantaneous events. They follow a predictable progression: a threat actor first scans for open ports, then probes for vulnerabilities, then establishes a foothold, and only then begins lateral movement or data exfiltration. Each stage leaves a distinct, measurable signature in network flow metadata.

PROGNOS captures these signatures without ever reading a single packet payload.

**The pipeline:**

1. **Zeek** monitors the network interface and outputs lightweight connection metadata to CSV logs. This includes TCP flags, packet counts, byte volumes, inter-arrival timing, and protocol behavior, grouped per connection. No payload is inspected. Encrypted HTTPS and VPN traffic is handled identically to plaintext traffic.

2. **The Sequence Chunker** groups Zeek output into 10-second rolling windows per source IP. Each window aggregates 30 statistical features. Six consecutive windows are stacked into a single temporal sequence, giving the model a 60-second view of any given source IP's behavior.

3. **The World Model** processes each 6-timestep sequence through a Feature Encoder (Linear + ReLU), then a single-layer LSTM, then a Native Attention mechanism. The LSTM's job is to learn what a Normal trajectory looks like and flag deviations from it. The Attention layer explicitly identifies which timestep within the 60-second window contained the most anomalous behavior.

4. **The Streamlit Dashboard** polls model predictions and maps them to the corresponding MITRE ATT&CK stage, displaying the attacker's trajectory, the active threat level, and the attention-highlighted feature that triggered the classification.

---

## Model Architecture

```
Input: (batch, 6 timesteps, 30 features)
       |
       v
Feature Encoder: Linear(30, 64) + ReLU + Dropout(0.2)
       |
       v
LSTM: input=64, hidden=128, layers=1, batch_first=True
       |
       v
Temporal Attention: Linear(128, 1) -> Softmax -> Weighted Context Vector
       |
      / \
     /   \
MITRE Classifier         Infiltration Probability Head
Linear(128, 64)          Linear(128, 32)
ReLU + Dropout(0.2)      ReLU
Linear(64, 5)            Linear(32, 1)
Softmax                  Sigmoid
     |                        |
MITRE Stage (0-4)       P(attack) in [0.0, 1.0]
```

**MITRE ATT&CK Output Classes:**

| Class | MITRE Tactic | Description |
| :--- | :--- | :--- |
| 0 | None | Normal baseline traffic |
| 1 | TA0043 Reconnaissance | Port scans, service enumeration |
| 2 | TA0001 Initial Access | Brute force, web attacks, SQL injection |
| 3 | TA0008 Lateral Movement | Internal pivoting, infiltration |
| 4 | TA0011 / TA0040 | Botnet C2, DDoS, volumetric attacks |

---

## Performance

Trained and evaluated on the CSE-CIC-IDS-2018 AWS Cloud dataset. The model was evaluated on a strict 20% held-out test split that was never seen during training.

| Metric | Score |
| :--- | :--- |
| Test Set Accuracy | 95.72% |
| Macro F1 | 0.7986 |
| Weighted F1 | 0.95 |

**Per-class breakdown:**

| Class | Precision | Recall | F1 |
| :--- | :--- | :--- | :--- |
| Normal | 0.96 | 0.99 | 0.97 |
| Initial Access | 0.97 | 1.00 | 0.99 |
| Lateral Movement | 0.47 | 0.17 | 0.25 |
| C2 / DDoS | 1.00 | 0.97 | 0.99 |

The lower Lateral Movement score is a known class imbalance artifact. The CIC-IDS-2018 dataset contains significantly fewer Infiltration samples than any other attack category, limiting the model's exposure to that class during training.

---

## Why Not Deep Packet Inspection?

DPI reads packet payloads. It cannot inspect encrypted traffic, it requires significant compute at scale, and it raises serious legal and privacy concerns in enterprise deployments. PROGNOS operates entirely on connection metadata: numbers describing *how* traffic flows, not *what* it contains. This means:

- Full compatibility with HTTPS, TLS 1.3, VPNs, and any encrypted protocol.
- Sub-15ms inference on CPU. No GPU required in production.
- Zero exposure to user data.
- Out-of-band passive monitoring. Zero changes required to the existing network.

---

## Applications

**Enterprise Security Operations Centers**
A SOC team receiving hundreds of alerts per shift cannot manually triage each one. PROGNOS reduces that burden by providing a pre-ranked, explainable threat trajectory rather than a flat stream of severity-sorted events. The Attention weights tell the analyst exactly which behavioral feature triggered the classification.

**Internet Service Providers**
ISPs monitoring backbone traffic can use PROGNOS to identify botnet-infected subscriber machines and volumetric DDoS origination points before they saturate upstream links.

**National CERTs and Government Infrastructure**
PROGNOS provides a sovereign, agentless monitoring layer for critical infrastructure (government servers, public banking systems, power grids) where installing endpoint agents on every machine is logistically impractical or politically infeasible.

**Cloud and Hybrid Environments**
The model was validated against an AWS-hosted network topology (CIC-IDS-2018), demonstrating that it generalizes beyond physical on-premise networks to modern cloud-native and hybrid-cloud environments without retraining.

---

## Tech Stack

| Component | Technology |
| :--- | :--- |
| Network Telemetry | Zeek (C++) |
| Data Processing | Python, Pandas, NumPy |
| Machine Learning | PyTorch (Linear Encoder, LSTM, Attention) |
| Scaling | Scikit-learn RobustScaler |
| Dashboard | Streamlit |
| Dataset | CSE-CIC-IDS-2017 / CSE-CIC-IDS-2018 |
| Labeling Standard | MITRE ATT&CK Framework v15.1 |

---

## Running the Project

### Requirements

```bash
pip install -r requirements.txt
```

### Run the Dashboard

```bash
streamlit run app.py
```

The dashboard will open at `http://localhost:8501`. A bundled replay CSV is included in the `Demo/` directory for demonstration purposes.

### Retraining the Model

This pipeline requires a machine with Zeek installed and the CIC-IDS-2018 PCAP files downloaded. It is provided for reproducibility.

```bash
# Step 1: Generate MITRE-labeled sequences from the Zeek PCAP logs
python ml/label_generator.py --mode cic2018 \
    --sequences data/sequences_2018.csv \
    --output data/master_2018_labeled.csv

# Step 2: Remove silent windows (dead traffic) and balance the dataset
python ml/perfect_downsample.py \
    --input data/master_2018_labeled.csv \
    --output data/balanced_sequences.pkl

# Step 3: Train the LSTM World Model
python ml/train_world_model.py --dataset data/balanced_sequences.pkl

# Step 4: Evaluate against the held-out test set
python ml/evaluate_world_model.py \
    --weights world_model_weights.pt \
    --dataset data/balanced_sequences.pkl
```

---

## Project Structure

```
PROGNOS/
├── app.py                       # Streamlit dashboard (main entry point)
├── world_model_weights.pt       # Pre-trained model weights
├── ml_scaler.pkl                # Fitted RobustScaler (required for inference)
├── ml/
│   ├── world_model.py           # PyTorch model architecture (Encoder + LSTM + Attention)
│   ├── train_world_model.py     # Training loop with 80/20 split
│   ├── evaluate_world_model.py  # Standalone test-set evaluation script
│   ├── label_generator.py       # MITRE ATT&CK labeling from CIC-IDS CSVs and IP mapping
│   ├── perfect_downsample.py    # Silence removal and class balancing
│   ├── dataset.py               # PyTorch Dataset and DataLoader
│   └── zeek_pipeline/
│       ├── sequence_chunker.py  # Groups Zeek logs into 10s temporal windows per IP
│       └── local.zeek           # Zeek policy script for metadata extraction
├── Demo/                        # Pre-recorded replay CSVs for live demo
├── data/                        # Training datasets (not included in repo due to size)
├── FINAL_RESULTS.md             # Final model performance report
└── requirements.txt
```

---

## Academic References

- Hochreiter, S. & Schmidhuber, J. (1997). Long Short-Term Memory. *Neural Computation*, 9(8), 1735-1780.
- Vaswani, A. et al. (2017). Attention Is All You Need. *NeurIPS 2017*.
- Sharafaldin, I. et al. (2018). Toward Generating a New Intrusion Detection Dataset and Intrusion Traffic Characterization. *ICISSP 2018*. (CIC-IDS-2018 Dataset)
- MITRE ATT&CK Framework, Version 15.1. https://attack.mitre.org
- Zeek Network Security Monitor. https://zeek.org
