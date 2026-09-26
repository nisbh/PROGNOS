import streamlit as st

def render_about_page():
    st.markdown("""
<style>
.about-hero {
    background: linear-gradient(135deg, var(--primary-dark) 0%, var(--secondary-dark) 100%);
    border-radius: 12px; padding: 40px; color: white;
    margin-bottom: 24px; box-shadow: 0 10px 25px rgba(11,23,42,0.15);
    border: 1px solid rgba(255,255,255,0.1);
}
.about-hero h1 { font-size: 32px; font-weight: 700; margin-bottom: 8px; }
.about-hero h3 { font-size: 16px; font-weight: 400; color: rgba(255,255,255,0.7); margin-bottom: 24px; letter-spacing: 1px; }
.about-hero p { font-size: 14px; line-height: 1.6; color: rgba(255,255,255,0.9); max-width: 800px; margin-bottom: 24px; }
.about-status-strip { display: flex; gap: 16px; font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; }
.about-status-item { display: flex; align-items: center; gap: 8px; background: rgba(255,255,255,0.1); padding: 6px 12px; border-radius: 6px; }

.about-section { margin-bottom: 40px; }
.about-section h2 { font-size: 18px; font-weight: 700; color: var(--primary-dark); margin-bottom: 16px; border-bottom: 2px solid var(--border); padding-bottom: 8px; }
.about-section p { font-size: 14px; color: var(--slate); line-height: 1.6; margin-bottom: 16px; }

.compare-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; margin-top: 20px; }
.compare-box { background: white; border: 1px solid var(--border); border-radius: 8px; padding: 24px; }
.compare-title { font-size: 12px; font-weight: 700; color: var(--muted); text-transform: uppercase; margin-bottom: 16px; letter-spacing: 1px; }
.compare-flow { display: flex; flex-direction: column; gap: 8px; align-items: center; }
.flow-node { background: var(--light-blue); color: var(--blue); padding: 8px 16px; border-radius: 6px; font-size: 12px; font-weight: 600; width: 100%; text-align: center; }
.flow-node.highlight { background: var(--primary-dark); color: white; }
.flow-arrow { color: var(--muted); font-size: 16px; }

.arch-container { display: flex; flex-direction: column; align-items: center; gap: 12px; padding: 20px; background: white; border-radius: 8px; border: 1px solid var(--border); }
.arch-block { border: 1px solid var(--blue); background: var(--light-blue); color: var(--blue); padding: 12px 24px; border-radius: 6px; width: 300px; text-align: center; font-weight: 600; font-size: 13px; }
.arch-desc { font-size: 11px; color: var(--slate); font-weight: 400; margin-top: 4px; }
.arch-arrow { color: var(--blue); font-weight: bold; }

.xai-demo { background: white; border: 1px solid var(--border); padding: 20px; border-radius: 8px; }
</style>
""", unsafe_allow_html=True)

    st.markdown("""
<div class="about-hero">
    <h1>PROGNOS</h1>
    <h3>EARLY WARNING SECURITY OPERATIONS CENTER</h3>
    <p>From network activity to attack trajectory. PROGNOS analyzes chronological network-flow telemetry to identify emerging threat trajectories and forecast potential attack progression before the attack reaches its later stages.</p>
    <div style="font-size: 13px; font-weight: 700; color: var(--blue); margin-bottom: 24px; letter-spacing: 2px;">
        OBSERVE &nbsp;→&nbsp; UNDERSTAND &nbsp;→&nbsp; FORECAST &nbsp;→&nbsp; EXPLAIN
    </div>
    <div class="about-status-strip">
        <div class="about-status-item"><span style="color:var(--success);">●</span> MODEL ONLINE</div>
        <div class="about-status-item"><span style="color:var(--light-blue);">●</span> NATIVE ATTENTION ACTIVE</div>
        <div class="about-status-item"><span style="color:var(--warning);">●</span> DATASET REPLAY</div>
    </div>
</div>
""", unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1])
    with col1:
        st.markdown("""
        <div class="about-section">
            <h2>THE LIMITATION OF REACTIVE DETECTION</h2>
            <p>Traditional security monitoring commonly focuses on identifying malicious behavior once recognizable indicators or signatures appear. PROGNOS approaches the problem from a temporal perspective.</p>
            <p>The important question becomes: <strong>"Is the network moving toward a dangerous state?"</strong></p>
            <div class="compare-grid" style="display:flex; flex-direction:column; gap:16px;">
                <div class="compare-box">
                    <div class="compare-title">TRADITIONAL DETECTION</div>
                    <div class="compare-flow">
                        <div class="flow-node" style="background:#F1F5F9; color:var(--slate);">Network Activity</div><div class="flow-arrow">↓</div>
                        <div class="flow-node" style="background:#F1F5F9; color:var(--slate);">Attack Occurs</div><div class="flow-arrow">↓</div>
                        <div class="flow-node" style="background:#FEE2E2; color:#991B1B;">Indicator Appears</div><div class="flow-arrow">↓</div>
                        <div class="flow-node" style="background:#FEF3C7; color:#92400E;">Alert Generated</div>
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class="about-section">
            <h2 style="color:transparent; border-bottom:none;">_</h2>
            <p>PROGNOS processes network-flow telemetry over time rather than treating every observation as an isolated event. The system builds chronological network-state sequences and uses a temporal deep-learning model to identify evolving patterns.</p>
            <p>This transforms the paradigm from reactive detection to proactive forecasting.</p>
            <div class="compare-grid" style="display:flex; flex-direction:column; gap:16px;">
                <div class="compare-box" style="border-color:var(--blue); box-shadow:0 4px 12px rgba(37,99,235,0.1);">
                    <div class="compare-title" style="color:var(--blue);">PROGNOS FORECASTING</div>
                    <div class="compare-flow">
                        <div class="flow-node">Network Activity</div><div class="flow-arrow">↓</div>
                        <div class="flow-node">Temporal Behavior</div><div class="flow-arrow">↓</div>
                        <div class="flow-node highlight">Trajectory Analysis</div><div class="flow-arrow">↓</div>
                        <div class="flow-node" style="background:var(--blue); color:white;">Early Warning Forecast</div>
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("""
    <div class="about-section">
        <h2>THE TEMPORAL WORLD MODEL</h2>
        <p>The core of PROGNOS is a custom deep-learning architecture that operates on 10-second sliding windows of Zeek network metadata. It does not require payload inspection, preserving privacy while analyzing flow-level behavior.</p>
        <div class="arch-container">
            <div class="arch-block">1D CNN<div class="arch-desc">Learns short-range local traffic patterns and bursts.</div></div>
            <div class="arch-arrow">↓</div>
            <div class="arch-block">LSTM<div class="arch-desc">Maintains temporal context and learns how network behavior evolves across sequential windows.</div></div>
            <div class="arch-arrow">↓</div>
            <div class="arch-block">NATIVE ATTENTION<div class="arch-desc">Highlights the portions of the temporal sequence that contribute most strongly to the current forecast.</div></div>
            <div class="arch-arrow">↓</div>
            <div class="arch-block highlight" style="background:var(--primary-dark); color:white; border-color:var(--primary-dark);">FORECAST ENGINE<div class="arch-desc" style="color:rgba(255,255,255,0.7);">Threat Probability & Stage Prediction</div></div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    col3, col4 = st.columns(2)
    with col3:
        st.markdown("""
        <div class="about-section">
            <h2>NATIVE TEMPORAL ATTENTION</h2>
            <p>Instead of relying solely on an external post-hoc explanation framework, PROGNOS uses an attention mechanism integrated directly into the temporal model. This provides a live view of which temporal signals and features are driving the current threat forecast.</p>
            <div class="xai-demo">
                <div style="font-size:10px; color:var(--muted); text-transform:uppercase; margin-bottom:12px; font-weight:600;">ILLUSTRATIVE ATTENTION WEIGHTS</div>
                <div class="attn-row"><div class="attn-header"><span>FLAG RST</span><span>82.4%</span></div><div class="attn-bg"><div class="attn-fill" style="width: 82.4%;"></div></div></div>
                <div class="attn-row"><div class="attn-header"><span>SYN RATE</span><span>65.1%</span></div><div class="attn-bg"><div class="attn-fill" style="width: 65.1%;"></div></div></div>
                <div class="attn-row"><div class="attn-header"><span>DURATION</span><span>41.2%</span></div><div class="attn-bg"><div class="attn-fill" style="width: 41.2%;"></div></div></div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown("""
        <div class="about-section">
            <h2>FROM FORECAST TO ATTACK LIFECYCLE</h2>
            <p>PROGNOS maps forecasted behavior to an attack-stage representation aligned with MITRE ATT&CK concepts. This allows SOC analysts to understand not just that an attack is occurring, but exactly where the adversary is in the intrusion lifecycle.</p>
            <div class="xai-demo" style="padding-top:40px; padding-bottom:40px;">
                <div class="atk-path">
                    <div class="atk-line"></div>
                    <div class="atk-node"><div class="atk-dot"></div><div class="atk-lbl">Normal</div></div>
                    <div class="atk-node"><div class="atk-dot"></div><div class="atk-lbl">Recon</div></div>
                    <div class="atk-node active"><div class="atk-dot active"></div><div class="atk-lbl">Initial Access</div></div>
                    <div class="atk-node"><div class="atk-dot"></div><div class="atk-lbl">Lateral Mvmt</div></div>
                    <div class="atk-node"><div class="atk-dot"></div><div class="atk-lbl">C2</div></div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("""
    <div class="about-section">
        <h2>CURRENT SYSTEM STATUS & VALIDATION</h2>
        <div class="compare-grid" style="grid-template-columns: 1fr 1fr 1fr;">
            <div class="compare-box">
                <div class="compare-title">TECHNOLOGY STACK</div>
                <div style="font-size:13px; color:var(--slate); line-height:1.8;">
                    <strong>Pipeline:</strong> Zeek, Pandas<br>
                    <strong>ML Engine:</strong> PyTorch (CNN-LSTM-Attn)<br>
                    <strong>Visualization:</strong> Streamlit, Plotly<br>
                    <strong>Artifact:</strong> world_model_weights.pt
                </div>
            </div>
            <div class="compare-box">
                <div class="compare-title">CURRENT IMPLEMENTATION</div>
                <div style="font-size:13px; color:var(--slate); line-height:1.8;">
                    ✓ Zeek telemetry parsing<br>
                    ✓ Temporal Model Inference<br>
                    ✓ Native Attention XAI<br>
                    ✓ MITRE Stage Representation<br>
                    ✓ Streamlit SOC Dashboard
                </div>
            </div>
            <div class="compare-box">
                <div class="compare-title">VALIDATION DATASET</div>
                <div style="font-size:13px; color:var(--slate); line-height:1.8;">
                    <strong>CIC-IDS-2017:</strong> Current Validation<br>
                    <strong>CIC-IDS-2018:</strong> Supported Format<br>
                    <strong>Traffic Type:</strong> Network Metadata<br>
                    <strong>Mode:</strong> Dataset Replay
                </div>
            </div>
        </div>
    </div>
    
    <div class="about-section" style="background: var(--white); border: 1px solid var(--border); padding: 32px; border-radius: 8px; text-align: center;">
        <h2 style="border:none; margin-bottom:8px;">BUILT FOR SMART INDIA HACKATHON 2026</h2>
        <p style="margin-bottom:0;">PROGNOS was developed as a proactive network-security forecasting solution for the SIH 2026 problem context.<br><strong>Problem:</strong> AI-based Network Attack Forecasting from Network Traffic Data.</p>
    </div>
    
    <div style="margin-top: 40px; padding-top: 16px; border-top: 1px solid var(--border); display: flex; justify-content: space-between; font-size: 10px; color: var(--muted); font-weight: 500; text-transform: uppercase;">
        <div>PROGNOS v2 • AI-Driven Early Warning Security Operations</div>
        <div>Zeek • PyTorch • CNN-LSTM • Native Attention</div>
        <div>MODEL: world_model_weights.pt • MODE: DATASET REPLAY</div>
    </div>
    """, unsafe_allow_html=True)
