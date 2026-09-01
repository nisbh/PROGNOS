# PROGNOS: Project Context & Handover Guide
This document contains the complete structural, technical, and strategic context of the PROGNOS platform. Use this as your primary source of truth for building the PPT and preparing for the judge Q&A session.

---

## 1. The Core Value Proposition
**What is PROGNOS?** 
PROGNOS is an AI-driven, early-warning Security Operations Center (SOC) dashboard. 

**The Problem it Solves:** 
Traditional SOC tools (like standard SIEMs) only trigger alerts *after* a threshold is breached or a signature matches—meaning the attack is already impacting the system. 

**The Innovation:** 
PROGNOS uses a machine learning model to detect the microscopic, early-stage precursor anomalies of an attack (like the initial ramp-up of a SYN flood or a slow port scan) and forecasts the attack *before* the traditional threshold is crossed.

---

## 2. The Tech Stack & Architecture

### Frontend (The Dashboard)
- **Framework:** React + TypeScript + Vite.
- **Styling:** TailwindCSS with a highly premium, dark-mode glassmorphic aesthetic to wow the judges.
- **Data Flow:** The frontend does not use WebSockets; it uses highly optimized **3-second polling** to pull the latest state from the FastAPI backend.
- **Key Components:**
  - **Live Threat Radar:** Visually tracks the transition from `NORMAL` -> `ELEVATED` -> `NEAR-TERM` -> `IMMINENT`.
  - **Live Traffic Trends:** An Area chart mapping the exact connection and SYN rates over time.
  - **Custom CSV Upload:** A button in the Sidebar allows judges to upload any network flow CSV to see the model analyze it in real-time.

### Backend (The Brain)
- **Framework:** FastAPI (Python) running on a Uvicorn ASGI server.
- **Data Engine:** Pandas is used for high-speed dataframe manipulation.
- **State Management:** The backend runs a continuous `async` background loop (`background_simulation_loop`) that ticks every 10 seconds. On each tick, it feeds the next row of the active CSV file into the ML model.

### AI / Machine Learning 
- **Model:** A highly optimized **XGBoost Classifier**.
- **Explainability:** **SHAP (Shapley Additive exPlanations)**. This is our secret weapon. Instead of the model being a "black box," SHAP mathematically breaks down *exactly* which network features (e.g., `syn_rate_1m_avg`) drove the prediction up or down.

---

## 3. Core Features for the Presentation

If you are building the PPT, these are the 4 pillars you must highlight:

### A. The "ELEVATED" State (Early Warning)
Most tools go from Green (Normal) directly to Red (Critical Alert). PROGNOS features an `ELEVATED` state. This represents the brief window of time where malicious reconnaissance or ramping is happening, but the attack hasn't hit full force. **Pitch angle:** *This is where we save companies millions of dollars—by catching the ramp-up.*

### B. Custom Replay Engine (Live Demo)
We built a `POST /upload-replay` endpoint. During the demo, you can click "Upload Custom CSV" in the sidebar, inject a completely new dataset, and the entire system instantly resets and begins analyzing the new attack vectors in real-time. 

### C. SHAP Explainable AI 
Technical judges will ask: *"How do you know it's a DDoS attack and not just a sudden spike in legitimate users?"* 
**The Answer:** Because our SHAP explainer isolates the exact features. If it was legitimate users, total bandwidth would spike. If it's a SYN flood, the SHAP explainer proves the model caught the disproportionate ratio of `syn_rate` to `connections_per_sec`. We show this exact mathematical reasoning live on the dashboard.

### D. MITRE ATT&CK Framework Mapping
We don't just throw raw ML numbers at analysts. We map the mathematical heuristics directly to defensible MITRE techniques:
- **T1498 (Network Denial of Service):** Mapped when `syn_rate` & `connections_per_sec` both spike simultaneously (SYN Floods).
- **T1499.004 (Endpoint Denial of Service):** Mapped when `avg_packet_size` spikes alongside connections (Application layer attacks like GoldenEye).
- **T1046 (Network Service Scanning):** Mapped during anomalous connection spikes without massive payload transfer.

---

## 4. Known Pitfalls & "Hard Truths" (For Defense)

You **must** be prepared for the judges to poke holes in the project. Here are our weaknesses and how to defend them:

1. **Weakness:** We are replaying a CSV instead of capturing live network packets (like PCAP) directly from the judge's laptop.
   - **Defense:** *"We built this as a SOC analysis engine, not a packet sniffer. In a real enterprise deployment, standard agents like Zeek or Argus sit at the network edge, convert PCAPs to flow statistics (the exact format of our CSV), and stream them to us. We built the engine to integrate with existing infrastructure, not replace it."*

2. **Weakness:** We only map to a few MITRE Tactics. Why not all 14?
   - **Defense:** *"It is mathematically impossible to detect techniques like 'Spearphishing' or 'Hardware Keyloggers' purely through volumetric network flow statistics. We explicitly constrained our model to Network-Layer attacks (DoS, Reconnaissance, C2) to ensure high fidelity and near-zero false positives."*

3. **Weakness:** The polling rate is 3 seconds, isn't that too slow for a 100Gbps network?
   - **Defense:** *"The 3-second polling is strictly for UI rendering so we don't crash the browser's DOM. The actual FastAPI backend processes dataframe inferences in milliseconds."*

---

## 5. API Endpoints (Quick Reference)
- `GET /current-status`: Returns the aggregate risk score and `NORMAL` vs `IMMINENT` state.
- `GET /forecast`: Returns the MITRE mappings and ETA to impact.
- `GET /explanation`: Returns the SHAP values (the "+0.86" or "-0.10" values) for the UI.
- `GET /history`: Returns the historical array for the Risk Score chart.
- `GET /traffic`: Returns the historical array for the network traffic charts.
- `POST /upload-replay`: Replaces the current data stream with a new user-provided CSV file.
