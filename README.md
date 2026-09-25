# 🛡️ PROGNOS v2: Deep Learning Early Warning SOC Dashboard

![SIH 2026](https://img.shields.io/badge/SIH-2026-blue?style=for-the-badge)
![PyTorch](https://img.shields.io/badge/PyTorch-%23EE4C2C.svg?style=for-the-badge&logo=PyTorch&logoColor=white)
![Zeek](https://img.shields.io/badge/Zeek-Security-000000?style=for-the-badge&logo=zeek)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=Streamlit&logoColor=white)

**PROGNOS v2** is a proactive Security Operations Center (SOC) dashboard built for the Smart India Hackathon (SIH) 2026. 

Unlike traditional SIEMs that rely on rigid threshold-based alerts (which only trigger *after* an attack causes damage), PROGNOS utilizes a custom **1D CNN + LSTM Deep Learning Architecture** equipped with a **Native Attention Mechanism**. It analyzes live chronological network flow telemetry to forecast cyberattacks in their earliest macroscopic stages (e.g., Reconnaissance and Initial Access) before catastrophic impact (e.g., volumetric DDoS or Exfiltration).

By capturing the temporal trajectory of an attacker, PROGNOS provides security analysts with a crucial multi-minute time window to mitigate threats before full-scale impact.

---

## 🔥 Key Technical Upgrades in v2

1. **Agentless Network Telemetry (Zeek):** We completely bypass Deep Packet Inspection (DPI). PROGNOS hooks into Zeek to extract 30 lightweight heuristic metadata features in real-time. This guarantees 100% data privacy (no payloads are read), seamlessly handles encrypted HTTPS/VPN traffic, and achieves ultra-low compute overhead (<15ms inference).
2. **Temporal World Model (CNN-LSTM):** We replaced the stateless v1 XGBoost model with a stateful LSTM that analyzes rolling 10-second chronological windows. The 1D CNN detects micro-bursts (e.g., SYN floods), while the LSTM remembers historical trajectories to distinguish legitimate flash crowds from low-and-slow APTs.
3. **Explainable AI (XAI) via Native Attention:** Instead of relying on slow, third-party explainers like SHAP, we engineered a native Attention Layer directly into the PyTorch network. This prevents the "vanishing gradient" problem on long sequences and pipes mathematical attention weights directly to the UI, proving exactly *why* the AI flagged an IP.
4. **MITRE ATT&CK Mapping:** Automatically maps underlying ML predictions directly to globally recognized adversarial stages (Reconnaissance $\rightarrow$ Initial Access $\rightarrow$ Lateral Movement $\rightarrow$ C2).
5. **Hybrid-Cloud Validation:** Mathematically proven across both localized enterprise network topologies (CIC-IDS-2017) and modern AWS Cloud topologies (CIC-IDS-2018).

---

## 🏗️ Architecture Stack

- **Data Pipeline:** Zeek (C++), Pandas Chunking Engine
- **Machine Learning Engine:** PyTorch (CNN, LSTM, Attention Layer), Scikit-Learn (RobustScaler)
- **UI & Visualization:** Streamlit, Altair, Plotly (Dynamic Glassmorphic SOC aesthetic)
- **Model Output:** `world_model_weights.pt` (Lightweight Frozen Weights for CPU Inference)

---

## 🚀 How to Run Locally

### 1. Environment Setup
```bash
# Clone the repository
git clone https://github.com/nisbh/PROGNOS.git
cd PROGNOS

# Install dependencies
pip install -r requirements.txt
```

### 2. Data Pipeline (Optional: To retrain from scratch)
If you wish to retrain the model on massive 15GB+ PCAP datasets without crashing your RAM, run the streaming pipeline:
```bash
# 1. Parse PCAPs using Zeek Docker container
# (Requires Docker Desktop)
Get-ChildItem -Path "data/raw_pcaps" -Filter *.pcap | ForEach-Object { docker run ... zeek ... }

# 2. Chunk Zeek logs into 10-second temporal trajectories
python ml\zeek_pipeline\sequence_chunker.py --input data\logs --output data\sequences.csv

# 3. Inject MITRE ATT&CK Labels natively (Bypasses academic CSV bugs)
python ml\label_generator.py --mode cic2018 --sequences data\sequences.csv --output data\master_labeled.csv --window 10

# 4. Downsample to optimize training
python ml\downsample.py --input data\master_labeled.csv --output data\train_ready.csv

# 5. Train the PyTorch CNN-LSTM Model
python ml\train_world_model.py --dataset data\train_ready.csv
```

### 3. Start the Streamlit SOC Dashboard
The frontend has been entirely rewritten in Streamlit for rapid, real-time Python integration.

```bash
# Run the live Streamlit dashboard
streamlit run dashboard.py
```
*The dashboard will automatically open at `http://localhost:8501`*

---

## 📂 Project Structure

```text
PROGNOS/
├── dashboard.py           # Streamlit Frontend UI and Live XAI Visualizations
├── ml/                    # Machine Learning Core
│   ├── train_world_model.py # PyTorch CNN-LSTM Architecture & Training Loop
│   ├── dataset.py         # PyTorch Dataloader and RobustScaler
│   ├── label_generator.py # MITRE ATT&CK answer key injection (Streaming)
│   ├── downsample.py      # RAM-safe traffic balancer
│   └── zeek_pipeline/     # Zeek PCAP parser and temporal sequence chunker
├── data/                  # Telemetry datasets
│   └── world_model_weights.pt # Pre-trained v2 AI Brain
└── ppts/                  # Reference presentations & SIH assets
```
