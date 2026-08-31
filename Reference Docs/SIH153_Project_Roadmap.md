# PS153 — AI-Based Network Attack Forecasting
## Project Roadmap v2 — Full Build Plan (Antigravity Context Doc)

**Status:** Nothing coded yet. Stack confirmed: Python/XGBoost backend, React frontend.
**Deadline:** Prototype fully working by end of Sept 1 (tomorrow night). Must run live for presentation on Sept 2.
**Team:** 1 cybersecurity/ML owner (me — learning ML as I build), 2 frontend/backend, 2 presentation/research.
**Round:** SIH internal round — judged on problem understanding, approach novelty, and feasibility, not production robustness.

This document is written to be handed directly to Antigravity as project context, and also to teach the ML side to a cybersecurity person with no prior ML background.

---

## 1. The problem, explained without jargon

Normal intrusion detection (IDS) says "an attack is happening right now." We're building something that says **"an attack is about to happen, and here's why we think so."**

Analogy: a weather app doesn't wait for rain to say "it's raining." It watches temperature, pressure, and humidity trending in a certain direction and forecasts rain *before* it starts. We do the same thing with network traffic: watch how traffic statistics are changing over the last few seconds, and forecast whether it's trending toward an attack.

**Non-negotiable framing for judges:** this must never look like "just an IDS with extra steps." The differentiator is *temporal trend* — we look at the last several windows of traffic and ask "is this getting worse," not just "is this window bad."

**Opening hook for the pitch:** in November 2025, Anthropic publicly disclosed that it disrupted the first documented large-scale AI-orchestrated cyber espionage campaign — a Chinese state-sponsored group used Claude Code to run attacks with up to 90% autonomy, with humans involved only for initial access and data exfiltration. That's real, verifiable, and a strong way to open: "attacks are now moving fast enough that reacting after the fact isn't good enough — this is why forecasting matters."

---

## 2. ML crash course (just enough to defend this on stage)

- **Feature**: a number describing something about a chunk of traffic (e.g. "connections per second"). The model sees rows of these numbers, not raw packets.
- **Label**: the correct answer used to train the model — "was this window followed by an attack soon after, yes or no."
- **Model (XGBoost)**: hundreds of small decision trees ("if SYN rate > X and unique IPs > Y, lean toward attack") voting together. Not a black-box neural net — closer to a very large, automatically-built flowchart. This is *why* it's explainable and why it trains in minutes, not hours.
- **Calibration**: making sure "80% probability" actually corresponds to ~80% of those cases really being attacks, via `CalibratedClassifierCV`. This is what lets you defend your percentages if a judge asks what "91%" actually means.
- **SHAP**: for each prediction, tells you which features pushed the model toward "attack" and by how much. Turns "the AI said so" into "the AI said so *because* SYN traffic jumped 700% and unique source IPs jumped 567%."

That's the full vocabulary you need.

---

## 3. Architecture (locked, unchanged after literature review)

```
Traffic source (pcap replay, real timestamps)
        │
        ▼
Feature extractor (SAME code for training AND live demo)
        │
        ▼
10-second non-overlapping windows
        │
        ▼
Feature vector: raw stats + rolling lag/trend features (last 3-5 windows)
        │
        ▼
Single multiclass XGBoost model
  classes: NORMAL / ELEVATED / NEAR-TERM / IMMINENT
        │
        ▼
CalibratedClassifierCV wrapper (sigmoid)
        │
        ▼
SHAP TreeExplainer → top contributing features
        │
        ▼
Asset-criticality multiplier (static JSON lookup by IP)
        │
        ▼
FastAPI REST endpoints (polling, no WebSockets)
        │
        ▼
Dashboard (React)
```

**Model decision, locked:** single multiclass XGBoost, not three separate binary models. Pitch the three-model version (independent horizon specialists, overlapping risk states) as the stated "production roadmap next step" — novelty credit without build risk.

We reviewed four additional papers/sources since the last version of this doc. None changed this architecture — they either operate at the wrong granularity (macro trend counts over months, not real-time flows), describe concepts too advanced to build in this timeframe (self-modifying agents, cyber ranges), or aren't credible technical sources at all. See Section 9 for what's actually worth citing in the presentation.

---

## 4. Data plan

- **Dataset:** CIC-IDS2017 (raw pcaps + flow labels — need the pcaps themselves for the demo replay, not just the pre-extracted CSV).
- **Labeling recipe (write this down exactly, you'll need to defend it on stage):**
  - IMMINENT = window falls within 0–30 sec before a labeled-attack window
  - NEAR-TERM = window falls within 30 sec–2 min before a labeled-attack window
  - ELEVATED = window falls within 2–5 min before a labeled-attack window
  - NORMAL = everything else; exclude windows too close to a boundary to avoid ambiguous labels
- **Critical rule:** feature extraction code must be *identical* for training data and live demo data. One function, two entry points (file replay vs. training batch) — never two separate implementations.
- **Validation split:** split chronologically (train on earlier time segment, test on later), never randomly. This is the single most defensible answer if a judge who knows ML asks about your evaluation method — random splits leak future information into training and inflate your reported accuracy.
- **Demo data:** pcap replay through the real pipeline, paced by original timestamps (`tcpreplay` or a small Python pacing script). Reliable, reproducible, immune to venue network issues.

---

## 5. Feature list (compute per 10-sec window)

**Raw window stats:**
- packet count, byte count, connection count
- unique source IPs, unique destination ports
- SYN packet count / rate
- failed-connection percentage
- TCP vs UDP connection ratio
- inbound/outbound byte ratio

**Trend features (computed from last 3–5 windows):**
- % change in connection count vs. previous window
- % change in SYN rate vs. previous window
- % change in unique source IPs vs. previous window
- rolling mean and rolling std of connection count over last 5 windows
- simple linear slope of SYN rate over last 5 windows

The trend features are what give you "forecasting" instead of "detection" — do not skip these.

---

## 6. Enterprise-value layers (cheap, high pitch value)

1. **Graduated multiclass risk** (already in architecture) — smooth escalation, not flat yes/no.
2. **Asset criticality weighting** — static JSON: `{"10.0.0.5": "crown_jewel", "10.0.0.12": "standard"}`. Multiply calibrated probability by a weight before final risk score. ~20 lines of code, huge pitch value.
3. **Calibrated probabilities** — `CalibratedClassifierCV(method='sigmoid')`. Two lines of code, defensible in Q&A.

---

## 7. API contract (backend builds against this, doesn't wait on model)

```
GET /current-status   → { risk_level, risk_score, class, ts }
GET /forecast          → { class, probability, eta_window, top_features: [...] }
GET /traffic            → recent window stats for the trend chart
GET /explanation        → SHAP top features for the current prediction
GET /history             → last N window classifications
```
Poll every 2–3 seconds from frontend. No WebSockets.

---

## 8. Full build timeline (starting from zero)

### Today (Aug 31) — remaining hours

**Block A — Data + labeling (start immediately):**
- Pull CIC-IDS2017 pcaps + flow labels
- Write the single feature-extractor function (raw stats only, no trend features yet)
- Implement the lookahead labeling rule from Section 4
- Checkpoint: print a handful of labeled rows, sanity-check the timeline makes sense before moving on

**Block B — Trend features + first model (same evening):**
- Add rolling/lag trend features on top of raw features
- Train a first-pass multiclass XGBoost, no calibration yet, just to confirm the pipeline runs end-to-end
- Checkpoint: model trains without errors, predictions look non-random on a held-out chronological slice

**Block C — Backend + frontend scaffolding (parallel, different people, same evening):**
- Backend member scaffolds all five FastAPI endpoints from Section 7 against hardcoded mock JSON
- Frontend member builds the dashboard against the mock endpoints — don't wait on the model
- Checkpoint: frontend renders a fake "HIGH RISK / DDoS / 91%" card end-to-end through the mock API

**End of today, minimum viable state:** labeled dataset exists, first model trains, mock API + dashboard talk to each other.

### Tomorrow (Sept 1) — full day, deadline is tonight

**Morning — Block D: Model hardening**
- Add `CalibratedClassifierCV` wrapper
- Add `shap.TreeExplainer`, confirm it returns sensible top features on test rows
- Handle class imbalance (NORMAL will dominate) with class weighting
- Checkpoint: calibration curve looks reasonable, SHAP output makes narrative sense (SYN rate, unique IPs should show up as top features for attack classes)

**Midday — Block E: Real integration**
- Connect real model output (not mocks) into the FastAPI endpoints
- Wire asset-criticality multiplier into the risk score
- Frontend swaps from mock data to real API
- Checkpoint: dashboard shows real model output end-to-end for a static test batch

**Afternoon — Block F: Replay harness (the demo backbone)**
- Build the pcap replay script (paced by original timestamps) feeding the real feature extractor
- Wire replay → trained model → API → dashboard, fully live
- Rehearse the full cycle at least 3 times back-to-back — confirm it reliably escalates through NORMAL → ELEVATED → NEAR-TERM → IMMINENT and fires at a consistent point each run
- Checkpoint: full demo cycle completes reliably, 3 runs in a row, no manual intervention needed

**Evening — Block G: Polish + presentation prep material**
- Asset-criticality demo beat: same traffic, two different "assets," different scores
- MITRE ATT&CK lookup table (hand to a presentation teammate to populate)
- One slide: confusion matrix or calibration curve as proof this is real, not hardcoded
- One slide: "traditional IDS vs. us" timeline comparison
- Record a backup video of the full demo cycle in case of AV/projector issues
- Checkpoint: prototype frozen, backup video recorded, full cycle timed at under 2 minutes

**This is the deadline point** — prototype must be fully working by end of tonight.

### Morning of presentation (Sept 2)
- Run the full cycle once more as a final sanity check, nothing else
- No new code — presentation day is for rehearsal, not development

---

## 9. Reference bank for the presentation (not for the build)

Keep this separate from the technical build — none of it changes the architecture, it's for slides and Q&A defense only.

| Source | Use it for | Notes |
|---|---|---|
| researchmethod.net predictive analytics guide | Methodology defense (chronological splits, calibration, common mistakes) | Solid general-methodology reference, safe to cite |
| Anthropic's Nov 2025 AI-orchestrated attack disclosure | Opening hook — why forecasting matters now | Real, verifiable event; strong motivational stat |
| Almahmoud et al. 2025 (long-term cyber-attack trend forecasting) | One-line citation that "forecasting vs. detection" is an active research direction | Don't adopt its methodology (it's macro/geopolitical trend forecasting, different problem) |
| DSPM/NRM IEEE Access paper | **Do not use** | Wrong granularity (aggregated counts, not flows), methodologically shaky, avoid citing |
| Darwin-Gödel Cyber Range paper (SimSpace/Oxford) | **Do not use for build**, optional single-line context only | Describes self-modifying autonomous SOC agents — different problem entirely, too advanced to reference as "related work" without confusing the pitch |
| "Forecasting Engine" patent content piece | **Do not use anywhere** | Reads as generated patent-marketing content, not a credible technical source; citing it risks your credibility |

---

## 10. What NOT to build (explicitly out of scope)

- LSTM/GRU/Transformer/GNN — mention only as a stated future direction
- WebSockets — REST polling only
- Live NIC packet capture — pcap replay only
- Self-modifying/autonomous agent architecture, cyber ranges — out of scope, different problem
- Real dark-web/OSINT data fusion — not in this scope
- Authentication, error hardening, edge cases — not judged at this stage

---

## 11. One-sentence pitch to open with

> "In November 2025, Anthropic disclosed that a state-sponsored group ran a large-scale cyberattack with 90% AI autonomy. Traditional IDS tells you an attack is happening — we tell you one is about to, why we believe that, and which asset actually matters."
