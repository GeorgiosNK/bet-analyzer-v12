import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# ==============================
# CONFIG & PROFESSIONAL CSS
# ==============================
st.set_page_config(page_title="Bet Analyzer v12.12.8 PRO", page_icon="⚽", layout="centered")

st.markdown("""
<style>
    [data-testid="stVerticalBlock"] > div:has(div.sticky-result) {
        position: sticky; top: 2.8rem; z-index: 1000;
        background: rgba(240, 242, 246, 0.98); padding-bottom: 10px;
    }
    .result-card {
        background: #ffffff; padding: 1rem; border-radius: 15px;
        border: 2px solid #1e3c72; box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        text-align: center;
    }
    .conf-bar { height: 12px; border-radius: 6px; background: #f0f2f6; overflow: hidden; position: relative; }
    .conf-fill { height: 100%; transition: width 0.8s ease-in-out; }
    .info-text {
        background-color: #e8f0fe; padding: 15px; border-radius: 10px;
        border-left: 5px solid #1e3c72; margin-bottom: 20px; font-size: 0.95rem;
    }
</style>
""", unsafe_allow_html=True)

# APP INFO TEXT
st.markdown("""
<div class="info-text">
    <strong>⚽ Bet Analyzer Pro: Σύστημα Στατιστικής Ανάλυσης Αγώνων</strong><br>
    Το Bet Analyzer είναι μια προηγμένη εφαρμογή ανάλυσης ποδοσφαιρικών αναμετρήσεων που συνδυάζει τα δεδομένα της στοιχηματικής αγοράς (Market Odds) με τα πραγματικά στατιστικά επιδόσεων των ομάδων (Real Stats). Στόχος της είναι να εντοπίζει την αξία (Value) και να προτείνει σημεία με την υψηλότερη πιθανότητα επιβεβαίωσης.
</div>
""", unsafe_allow_html=True)

# ==============================
# INITIALIZATION & RESET LOGIC
# ==============================
if 'hw' not in st.session_state:
    st.session_state.update({'hw':0, 'hd':0, 'hl':0, 'aw':0, 'ad':0, 'al':0})
if 'o1_val' not in st.session_state:
    st.session_state.update({'o1_val': "1.00", 'ox_val': "1.00", 'o2_val': "1.00"})

def reset_everything():
    # Επαναφορά στατιστικών
    for k in ['hw','hd','hl','aw','ad','al']: 
        st.session_state[k] = 0
    # Επαναφορά αποδόσεων στο 1.00
    st.session_state.o1_val = "1.00"
    st.session_state.ox_val = "1.00"
    st.session_state.o2_val = "1.00"

# ==============================
# SIDEBAR
# ==============================
with st.sidebar:
    st.markdown("### 🏆 Bet Analyzer Pro")
    st.caption("Version 12.12.8 • Full Reset Support")
    st.divider()
    
    # Το κουμπί τώρα καλεί τη συνάρτηση που τα μηδενίζει όλα
    st.button("🧹 Clear All Stats & Odds", on_click=reset_everything, use_container_width=True)
    
    st.header("📊 Αποδόσεις (Odds)")
    o1_raw = st.text_input("Άσος (1)", key="o1_val")
    ox_raw = st.text_input("Ισοπαλία (X)", key="ox_val")
    o2_raw = st.text_input("Διπλό (2)", key="o2_val")
    
    try:
        # Αντικατάσταση κόμματος και μετατροπή. 
        # Χρησιμοποιούμε max(1.0, ...) για να αποφύγουμε διαίρεση με το μηδέν
        ace_odds = max(1.0, float(o1_raw.replace(',', '.')))
        draw_odds = max(1.0, float(ox_raw.replace(',', '.')))
        double_odds = max(1.0, float(o2_raw.replace(',', '.')))
    except:
        ace_odds = draw_odds = double_odds = 1.00

# ==============================
# LOGIC ENGINE
# ==============================
h_total = st.session_state.hw + st.session_state.hd + st.session_state.hl
a_total = st.session_state.aw + st.session_state.ad + st.session_state.al
total_all = h_total + a_total
is_blind = (total_all == 0)

# Υπολογισμός πιθανοτήτων αγοράς
inv_odds = (1/ace_odds + 1/draw_odds + 1/double_odds)
prob_1, prob_X, prob_2 = (1/ace_odds)/inv_odds, (1/draw_odds)/inv_odds, (1/double_odds)/inv_odds

if is_blind:
    real_1, real_X, real_2 = prob_1, prob_X, prob_2
    h_pos, a_pos = 0.5, 0.5
    mode_label = "⚖️ BLIND MODE • ΠΡΟΤΑΣΗ"
else:
    real_1 = st.session_state.hw/h_total if h_total > 0 else 0
    real_X = (st.session_state.hd + st.session_state.ad)/total_all if total_all > 0 else 0
    real_2 = st.session_state.aw/a_total if a_total > 0 else 0
    h_pos = (st.session_state.hw + st.session_state.hd)/h_total if h_total > 0 else 0
    a_pos = (st.session_state.aw + st.session_state.ad)/a_total if a_total > 0 else 0
    mode_label = "⚖️ ΣΤΑΤΙΣΤΙΚΗ ΥΠΕΡΟΧΗ • ΠΡΟΤΑΣΗ"

# Priority Logic
if not is_blind:
    if real_X > 0.40: proposal = "X (1X)" if real_1 > real_2 else "X (X2)"
    elif real_X < 0.15: proposal = "1-2"
    elif h_pos >= 2 * a_pos: proposal = "1X"
    elif a_pos >= 2 * h_pos: proposal = "X2"
    else: proposal = "1X" if real_1 >= real_2 else "X2"
else:
    proposal = "1X" if prob_1 >= prob_2 else "X2"

confidence = max(5, min(100, int((1 - abs(real_1 - prob_1) - abs(real_2 - prob_2)) * 100)))

# ==============================
# STICKY HEADER
# ==============================
color = "#f1c40f" if confidence < 75 else "#2ecc71"
st.markdown(f"""
<div class="sticky-result">
    <div class="result-card">
        <div style="font-size: 0.75rem; color: #666; font-weight:bold;">{mode_label}</div>
        <div style="font-size: 2.5rem; font-weight: 900; color: #1e3c72; margin: 5px 0;">{proposal}</div>
        <div style="display: flex; align-items: center; gap: 15px; justify-content: center;">
            <div class="conf-bar" style="flex-grow: 1; max-width: 300px;">
                <div class="conf-fill" style="width: {confidence}%; background: {color};"></div>
            </div>
            <div style="font-size: 1.2rem; font-weight: 800; color: {color};">{confidence}%</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ==============================
# MAIN INPUTS
# ==============================
st.markdown("### 📝 Στατιστικά Ομάδων")
c1, c2 = st.columns(2)
with c1:
    st.markdown("**🏠 Γηπεδούχος**")
    st.number_input("Εντός_Νίκες (H)", 0, 100, key="hw")
    st.number_input("Εντός_Ισοπαλίες (H)", 0, 100, key="hd")
    st.number_input("Εντός_Ήττες (H)", 0, 100, key="hl")
with c2:
    st.markdown("**🚀 Φιλοξενούμενος**")
    st.number_input("Εκτός_Νίκες (A)", 0, 100, key="aw")
    st.number_input("Εκτός_Ισοπαλίες (A)", 0, 100, key="ad")
    st.number_input("Εκτός_Ήττες (A)", 0, 100, key="al")

# ==============================
# CHART
# ==============================
with st.expander("📊 Ανάλυση & Γράφημα", expanded=True):
    fig = go.Figure()
    x_labels = ["1", "X", "2"]
    
    fig.add_trace(go.Bar(
        name='Market', x=x_labels, y=[prob_1*100, prob_X*100, prob_2*100], 
        marker_color='#FF4B4B', text=[f"{prob_1*100:.1f}%", f"{prob_X*100:.1f}%", f"{prob_2*100:.1f}%"],
        textposition='inside', insidetextfont=dict(color='white', size=12, family="Arial Black")
    ))
    
    fig.add_trace(go.Bar(
        name='Stats', x=x_labels, y=[real_1*100, real_X*100, real_2*100], 
        marker_color='#0083B0', text=[f"{real_1*100:.1f}%", f"{real_X*100:.1f}%", f"{real_2*100:.1f}%"],
        textposition='inside', insidetextfont=dict(color='white', size=12, family="Arial Black")
    ))

    fig.update_layout(
        barmode='group', height=350, margin=dict(l=10, r=10, t=10, b=10),
        xaxis=dict(type='category', tickmode='array', tickvals=x_labels),
        yaxis=dict(range=[0, 100]),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig, use_container_width=True)
