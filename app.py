import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import streamlit.components.v1 as components

# ==============================
# CONFIG & PROFESSIONAL CSS
# ==============================
st.set_page_config(page_title="Bet Analyzer v12.13.5 PRO", page_icon="⚽", layout="centered")

# JavaScript για Auto-select on focus
components.html(
    """
    <script>
        const setupAutoSelect = () => {
            const inputs = window.parent.document.querySelectorAll('input[type="number"]');
            inputs.forEach(input => {
                input.addEventListener('focus', function() { this.select(); });
                input.addEventListener('click', function() { this.select(); });
            });
        }
        setTimeout(setupAutoSelect, 1000);
    </script>
    """,
    height=0,
)

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
    .info-text {
        background-color: #e8f0fe; padding: 15px; border-radius: 10px;
        border-left: 5px solid #1e3c72; margin-bottom: 20px; font-size: 0.95rem;
    }
    .warning-box {
        background-color: #fff3cd; color: #856404; padding: 12px; 
        border-radius: 8px; border: 1px solid #ffeeba; margin-top: 10px; 
        font-weight: bold; text-align: center; font-size: 0.9rem;
    }
    .pos-badge {
        background: #1e3c72; color: white; padding: 2px 8px; 
        border-radius: 5px; font-size: 0.85rem; margin-left: 10px;
    }
    .guide-item { padding: 12px; margin: 10px 0; border-radius: 8px; font-size: 0.9rem; }
</style>
""", unsafe_allow_html=True)

# APP INFO TEXT
st.markdown("""
<div class="info-text">
    <strong>⚽ Bet Analyzer Pro v12.13.5</strong><br>
    Ο Bet Analyzer συνδυάζει Market Odds & Real Stats με πλήρη στατιστική απεικόνιση και αυτόματη επιλογή πεδίων.
</div>
""", unsafe_allow_html=True)

# ==============================
# INITIALIZATION & RESET LOGIC
# ==============================
if 'hw' not in st.session_state: st.session_state.update({'hw':0, 'hd':0, 'hl':0, 'aw':0, 'ad':0, 'al':0})
if 'o1_num' not in st.session_state: st.session_state.update({'o1_num': 1.00, 'ox_num': 1.00, 'o2_num': 1.00})

def reset_everything():
    for k in ['hw','hd','hl','aw','ad','al']: st.session_state[k] = 0
    st.session_state.o1_num = 1.00
    st.session_state.ox_num = 1.00
    st.session_state.o2_num = 1.00

# ==============================
# SIDEBAR
# ==============================
with st.sidebar:
    st.markdown("### 🏆 Bet Analyzer Pro")
    st.caption("Version 12.13.5 PRO")
    st.divider()
    st.button("🧹 Clear All Stats & Odds", on_click=reset_everything, use_container_width=True)
    st.header("📊 Αποδόσεις (Odds)")
    ace_odds = st.number_input("Άσος (1)", min_value=1.0, step=0.01, format="%.2f", key="o1_num")
    draw_odds = st.number_input("Ισοπαλία (X)", min_value=1.0, step=0.01, format="%.2f", key="ox_num")
    double_odds = st.number_input("Διπλό (2)", min_value=1.0, step=0.01, format="%.2f", key="o2_num")

# ==============================
# LOGIC ENGINE
# ==============================
ace_odds, draw_odds, double_odds = max(1.0, ace_odds), max(1.0, draw_odds), max(1.0, double_odds)
h_total = st.session_state.hw + st.session_state.hd + st.session_state.hl
a_total = st.session_state.aw + st.session_state.ad + st.session_state.al

inv_odds = (1/ace_odds + 1/draw_odds + 1/double_odds)
prob_1, prob_X, prob_2 = (1/ace_odds)/inv_odds, (1/draw_odds)/inv_odds, (1/double_odds)/inv_odds

h_pos = (st.session_state.hw + st.session_state.hd)/h_total if h_total > 0 else 0
a_pos = (st.session_state.aw + st.session_state.ad)/a_total if a_total > 0 else 0

if (h_total + a_total) == 0:
    real_1, real_X, real_2 = prob_1, prob_X, prob_2
    mode_label, proposal = "⚖️ BLIND MODE • ΠΡΟΤΑΣΗ", ("1 (1X)" if prob_1 >= prob_2 else "2 (X2)")
else:
    # Υπολογισμός ποσοστών ανά κατηγορία
    r1 = st.session_state.hw/h_total if h_total > 0 else 0
    r2 = st.session_state.aw/a_total if a_total > 0 else 0
    rx = ((st.session_state.hd/h_total if h_total > 0 else 0) + (st.session_state.ad/a_total if a_total > 0 else 0)) / 2
    
    # Normalization για το γράφημα
    total_r = r1 + rx + r2
    real_1, real_X, real_2 = (r1/total_r, rx/total_r, r2/total_r) if total_r > 0 else (0,0,0)

    mode_label = "⚖️ ΣΤΑΤΙΣΤΙΚΗ ΥΠΕΡΟΧΗ • ΠΡΟΤΑΣΗ"
    if real_X >= 0.40: proposal = "X (X2)" if a_pos >= 2 * h_pos and a_pos > 0 else "X (1X)"
    elif real_X < 0.15: proposal = f"{'1' if real_1 >= real_2 else '2'} (1-2)"
    elif real_1 > 0.45 and real_2 > 0.45: proposal = "1 (1-2)"
    elif a_pos >= 2 * h_pos and a_pos > 0: proposal = "2 (X2)"
    elif h_pos >= 2 * a_pos and h_pos > 0: proposal = "1 (1X)"
    else: proposal = "1 (1X)" if h_pos >= a_pos else "2 (X2)"

    warning_msg = ""
    if (real_1 + real_2) < 0.40:
        warning_msg = "⚠️ HIGH RISK MATCH: Statistics are very low, abstention is recommended."
        mode_label += " (Low Confidence)"
    if ace_odds <= 1.50 and real_X > 0.25: warning_msg = "⚠️ TRAP στο Χ: Ένδειξη ότι το φαβορί θα δυσκολευτεί."

confidence = max(5, min(100, int((1 - abs(real_1 - prob_1) - abs(real_2 - prob_2)) * 100)))
color = "#2ecc71" if confidence >= 80 else "#f1c40f" if confidence >= 60 else "#e74c3c"

# ==============================
# STICKY HEADER & RESULTS
# ==============================
st.markdown(f"""
<div class="sticky-result">
<div class="result-card">
<div style="font-size: 0.75rem; color: #666; font-weight:bold; margin-bottom: 2px;">{mode_label}</div>
<div style="font-size: 3.5rem; font-weight: 900; color: #1e3c72; line-height: 1; margin: 0;">{proposal}</div>
<div style="font-size: 1.6rem; font-weight: 900; color: {color}; margin-bottom: 10px;">{confidence}%</div>
<div style="max-width: 550px; margin: 0 auto;">
<div style="width: 100%; height: 32px; background: #f0f2f6; position: relative; border-radius: 16px; border: 1px solid #ddd; overflow: hidden;">
<div style="width: {confidence}%; background: {color}; height: 100%; transition: width 0.8s ease-in-out;"></div>
<div style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; display: flex; align-items: center; justify-content: center;">
<span style="color: white; font-weight: 900; font-size: 1rem; text-shadow: -1px -1px 0 #000, 1px -1px 0 #000, -1px 1px 0 #000, 1px 1px 0 #000;">CONFIDENCE BAR</span>
</div></div></div></div></div>
""", unsafe_allow_html=True)

# ==============================
# MAIN INPUTS
# ==============================
st.markdown("### 📝 Στατιστικά Ομάδων")
c1, c2 = st.columns(2)
with c1:
    st.markdown(f'**🏠 Γηπεδούχος** <span class="pos-badge">{h_pos*100:.1f}% Positive</span>', unsafe_allow_html=True)
    st.number_input("Εντός_Νίκες", 0, 100, key="hw")
    st.number_input("Εντός_Ισοπαλίες", 0, 100, key="hd")
    st.number_input("Εντός_Ήττες", 0, 100, key="hl")
with c2:
    st.markdown(f'**🚀 Φιλοξενούμενος** <span class="pos-badge">{a_pos*100:.1f}% Positive</span>', unsafe_allow_html=True)
    st.number_input("Εκτός_Νίκες (A)", 0, 100, key="aw")
    st.number_input("Εκτός_Ισοπαλίες (A)", 0, 100, key="ad")
    st.number_input("Εκτός_Ήττες (A)", 0, 100, key="al")

# ==============================
# TABS
# ==============================
tab1, tab2 = st.tabs(["📊 Ανάλυση & Γράφημα", "🛡️ Οδηγός Στρατηγικής"])
with tab1:
    fig = go.Figure()
    categories = ["1", "X", "2"]
    
    fig.add_trace(go.Bar(
        name='Booker_Odds', x=categories, y=[prob_1*100, prob_X*100, prob_2*100], 
        marker_color='#FF4B4B', text=[f"{prob_1*100:.1f}%", f"{prob_X*100:.1f}%", f"{prob_2*100:.1f}%"], 
        textposition='auto', insidetextfont=dict(color='white')
    ))
    fig.add_trace(go.Bar(
        name='Performance_Stats', x=categories, y=[real_1*100, real_X*100, real_2*100], 
        marker_color='#0083B0', text=[f"{real_1*100:.1f}%", f"{real_X*100:.1f}%", f"{real_2*100:.1f}%"], 
        textposition='auto', insidetextfont=dict(color='white')
    ))
    
    fig.update_layout(
        barmode='group', height=350, margin=dict(l=10, r=10, t=10, b=10),
        xaxis=dict(type='category', categoryorder='array', categoryarray=categories),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.markdown("""
    <div class="guide-item" style="border-left: 5px solid #2ecc71; background: rgba(46, 204, 113, 0.1);">
        <strong style="color: #2ecc71;">Confidence >80% (Πράσινο):</strong> Κύρια Επιλογή.
    </div>
    <div class="guide-item" style="border-left: 5px solid #f1c40f; background: rgba(241, 196, 15, 0.1);">
        <strong style="color: #d4ac0d;">Confidence 61-79% (Κίτρινο):</strong> Χρειάζεται κάλυψη.
    </div>
    <div class="guide-item" style="border-left: 5px solid #e74c3c; background: rgba(231, 76, 60, 0.1);">
        <strong style="color: #e74c3c;">Confidence <60% (Κόκκινο):</strong> Υψηλό ρίσκο.
    </div>
    """, unsafe_allow_html=True)
