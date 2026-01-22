import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- CONFIGURATION & STYLING ---
st.set_page_config(page_title="Real Stats Predictor v17.2.0", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stMetric { background-color: #ffffff; padding: 20px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

def run_analysis():
    st.title("⚽ Real Stats Analysis v17.2.0")
    
    # --- INPUT SECTION ---
    with st.sidebar:
        st.header("📌 Αποδόσεις Bookie")
        o1 = st.number_input("Άσος (1)", value=2.70, format="%.2f")
        oX = st.number_input("Ισοπαλία (X)", value=3.60, format="%.2f")
        o2 = st.number_input("Διπλό (2)", value=2.50, format="%.2f")
        
        st.divider()
        st.header("🏠 Γηπεδούχος")
        h_w = st.number_input("Νίκες (Ε)", value=3, step=1)
        h_d = st.number_input("Ισοπαλίες (Ε)", value=0, step=1)
        h_l = st.number_input("Ήττες (Ε)", value=0, step=1)
        
        st.header("🚀 Φιλοξενούμενος")
        a_w = st.number_input("Νίκες (Φ)", value=1, step=1)
        a_d = st.number_input("Ισοπαλίες (Φ)", value=1, step=1)
        a_l = st.number_input("Ήττες (Φ)", value=1, step=1)

    # --- CALCULATIONS (LOGIC) ---
    # 1. Bookie Probabilities
    total_implied = (1/o1) + (1/oX) + (1/o2)
    p1_b, pX_b, p2_b = (1/o1)/total_implied, (1/oX)/total_implied, (1/o2)/total_implied

    # 2. Real Stats (v17.2.0 Core)
    h_tot, a_tot = (h_w + h_d + h_l), (a_w + a_d + a_l)
    
    if h_tot == 0 or a_tot == 0:
        st.error("⚠️ HIGH RISK MATCH: Statistics are very low, abstention is recommended.")
        return

    p1_r = h_w / h_tot
    pX_r = (h_d + a_d) / (h_tot + a_tot)
    p2_r = a_w / a_tot
    
    # Alpha Calibration 0.5
    p1_f = (p1_r * 0.5) + (p1_b * 0.5)
    pX_f = (pX_r * 0.5) + (pX_b * 0.5)
    p2_f = (p2_r * 0.5) + (p2_b * 0.5)
    
    norm = p1_f + pX_f + p2_f
    p1, pX, p2 = p1_f/norm, pX_f/norm, p2_f/norm

    # 3. DECISION LOGIC (ΟΙ ΚΑΝΟΝΕΣ ΣΟΥ)
    if (p1 + p2) < 0.40:
        st.warning("⚠️ HIGH RISK MATCH: Statistics are very low, abstention is recommended.")
    
    # Προσδιορισμός Κυρίαρχου
    if p1 > pX and p1 > p2: primary, p_odds = "1", o1
    elif p2 > p1 and p2 > pX: primary, p_odds = "2", o2
    else: primary, p_odds = "X", oX

    # ΚΑΝΟΝΑΣ: Κάλυψη αν απόδοση >= 2.80 και υπάρχει "σχισμή" (v17.2.0)
    if p_odds >= 2.80:
        if primary == "1" and (pX > 0.10 or a_d > 0): suggestion = "1 (1X)"
        elif primary == "2" and (pX > 0.10 or h_d > 0): suggestion = "2 (X2)"
        else: suggestion = primary
    else:
        suggestion = primary

    # ΚΑΝΟΝΑΣ: Real Stat X > 40%
    if pX > 0.40 and "X" not in suggestion:
        suggestion = "X" if pX > p1 and pX > p2 else f"{suggestion}X"

    # ΚΑΝΟΝΑΣ: Positive Percentage Double -> X2 ή 1X
    h_pos = (h_w + h_d) / h_tot
    a_pos = (a_w + a_d) / a_tot
    if a_pos >= 2 * h_pos and h_pos > 0: suggestion = "X2"
    elif h_pos >= 2 * a_pos and a_pos > 0: suggestion = "1X"

    # ΚΑΝΟΝΑΣ: Real 1 & Real 2 > 45% ή Real X < 15% -> 1-2
    if (p1 > 0.45 and p2 > 0.45) or pX < 0.15:
        suggestion = "1-2"

    # --- UI DISPLAY ---
    col_res1, col_res2 = st.columns([1, 2])
    
    with col_res1:
        st.metric("Πρόταση", f"{suggestion} (VALUE)")
        conf = int(max(p1, pX, p2) * 100)
        st.write(f"**Confidence:** {conf}%")
        
        if o1 <= 1.50 and pX > 0.25:
            st.warning("⚠️ TRAP στο Χ: Ο φαβορί θα δυσκολευτεί!")

    with col_res2:
        fig = go.Figure(data=[
            go.Bar(name='Bookie %', x=['1', 'X', '2'], y=[p1_b*100, pX_b*100, p2_b*100], marker_color='#b2bec3'),
            go.Bar(name='Real Stats %', x=['1', 'X', '2'], y=[p1*100, pX*100, p2*100], marker_color='#00b894')
        ])
        fig.update_layout(barmode='group', height=300, margin=dict(l=20, r=20, t=20, b=20))
        st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    run_analysis()
