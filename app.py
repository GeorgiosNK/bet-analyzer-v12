import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import streamlit.components.v1 as components

# ==============================
# CONFIG & DYNAMIC THEME UI
# ==============================
st.set_page_config(page_title="Bet Analyzer v12.14.6 MASTER", page_icon="⚽", layout="centered")

# Auto-select JavaScript
components.html(
    """
    <script>
        const setupAutoSelect = () => {
            const inputs = window.parent.document.querySelectorAll('input');
            inputs.forEach(input => {
                input.addEventListener('focus', function() { this.select(); });
            });
        }
        setTimeout(setupAutoSelect, 1000);
    </script>
    """,
    height=0,
)

st.markdown("""
<style>
    /* Sticky Header Logic */
    [data-testid="stVerticalBlock"] > div:has(div.sticky-result) {
        position: sticky; top: 2.8rem; z-index: 1000;
        background: transparent; padding-bottom: 10px;
    }
    
    /* FIX: Force Dark Background on Card in Dark Mode */
    @media (prefers-color-scheme: dark) {
        .result-card {
            background-color: #1a1c23 !important; /* Σκούρο φόντο */
            border: 2px solid #3498db !important;
            box-shadow: 0 0 20px rgba(52, 152, 219, 0.4) !important;
            color: #ffffff !important;
        }
        .result-card .mode-label { color: #3498db !important; }
        .result-card .proposal-text { color: #ffffff !important; }
    }
    
    /* Light Mode Style */
    @media (prefers-color-scheme: light) {
        .result-card {
            background-color: #ffffff !important;
            border: 2px solid #1e3c72 !important;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1) !important;
            color: #1e3c72 !important;
        }
        .result-card .mode-label { color: #666 !important; }
        .result-card .proposal-text { color: #1e3c72 !important; }
    }

    .result-card { padding: 1.5rem; border-radius: 15px; text-align: center; margin-bottom: 15px; }
    
    .info-text {
        background: rgba(52, 152, 219, 0.1); padding: 15px; border-radius: 10px;
        border-left: 5px solid #3498db; margin-bottom: 20px; font-size: 0.95rem;
    }
    
    .warning-box {
        background-color: rgba(231, 76, 60, 0.1); color: #e74c3c; padding: 12px; 
        border-radius: 8px; border: 1px solid #e74c3c; margin-top: 10px; 
        font-weight: bold; text-align: center; font-size: 0.9rem;
    }
    
    .pos-badge {
        background: #1e3c72; color: white; padding: 3px 10px; 
        border-radius: 5px; font-size: 0.85rem; margin-left: 10px; font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="info-text">
    <strong>⚽ Bet Analyzer Pro v12.14.6</strong><br>
    Συνδυασμός Market Odds και Real Stats για βέλτιστη ανάλυση ποδοσφαιρικών αναμετρήσεων.
</div>
""", unsafe_allow_html=True)

# ==============================
# STATE & DATA
# ==============================
if 'hw' not in st.session_state: st.session_state.update({'hw':0, 'hd':0, 'hl':0, 'aw':0, 'ad':0, 'al':0})
if 'o1_str' not in st.session_state: st.session_state.update({'o1_str': "1.00", 'ox_str': "1.00", 'o2_str': "1.00"})

def reset_everything():
    for k in ['hw','hd','hl','aw','ad','al']: st.session_state[k] = 0
    st.session_state.o1_str = "1.00"; st.session_state.ox_str = "1.00"; st.session_state.o2_str = "1.00"

# ==============================
# SIDEBAR
# ==============================
with st.sidebar:
    st.markdown("### 🏆 Bet Analyzer Pro")
    st.caption("Version 12.14.6 MASTER")
    st.divider()
    st.button("🧹 Clear All Stats & Odds", on_click=reset_everything, use_container_width=True)
    st.header("📊 Αποδόσεις (Odds)")
    o1_txt = st.text_input("Άσος (1)", key="o1_str")
    ox_txt = st.text_input("Ισοπαλία (X)", key="ox_str")
    o2_txt = st.text_input("Διπλό (2)", key="o2_str")

def safe_float(val):
    try: return float(str(val).replace(',', '.'))
    except: return 1.00

ace_odds = max(1.0, safe_float(o1_txt))
draw_odds = max(1.0, safe_float(ox_txt))
double_odds = max(1.0, safe_float(o2_txt))

# ==============================
# LOGIC ENGINE
# ==============================
h_total = st.session_state.hw + st.session_state.hd + st.session_state.hl
a_total = st.session_state.aw + st.session_state.ad + st.session_state.al
total_all = h_total + a_total

inv_odds = (1/ace_odds + 1/draw_odds + 1/double_odds)
prob_1, prob_X, prob_2 = (1/ace_odds)/inv_odds, (1/draw_odds)/inv_odds, (1/double_odds)/inv_odds

h_pos = (st.session_state.hw + st.session_state.hd)/h_total if h_total > 0 else 0
a_pos = (st.session_state.aw + st.session_state.ad)/a_total if a_total > 0 else 0

warning_msg, proposal, mode_label = "", "", ""

if total_all == 0:
    real_1, real_X, real_2 = prob_1, prob_X, prob_2
    mode_label, proposal = "⚖️ BLIND MODE • ΠΡΟΤΑΣΗ", ("1 (1X)" if prob_1 >= prob_2 else "2 (X2)")
else:
    r1, r2 = st.session_state.hw/h_total if h_total > 0 else 0, st.session_state.aw/a_total if a_total > 0 else 0
    rx = ((st.session_state.hd/h_total if h_total > 0 else 0) + (st.session_state.ad/a_total if a_total > 0 else 0)) / 2
    tr = r1 + rx + r2
    real_1, real_X, real_2 = (r1/tr, rx/tr, r2/tr) if tr > 0 else (0,0,0)
    mode_label = "⚖️ ΣΤΑΤΙΣΤΙΚΗ ΥΠΕΡΟΧΗ • ΠΡΟΤΑΣΗ"
    
    # 1. Real Stat X > 40%
    if real_X > 0.40:
        proposal = "X (X2)" if a_pos >= 2 * h_pos and a_pos > 0 else "X (1X)"
    # 2. Real Stat X < 15%
    elif real_X < 0.15:
        proposal = f"{'1' if real_1 >= real_2 else '2'} (1-2)"
    # 3. Both Ace/Double > 45%
    elif real_1 > 0.45 and real_2 > 0.45:
        proposal = "1 (1-2)"
    # 4. Double Positive Percentage
    elif a_pos >= 2 * h_pos and a_pos > 0:
        proposal = "2 (X2)"
    elif h_pos >= 2 * a_pos and h_pos > 0:
        proposal = "1 (1X)"
    else:
        proposal = "1 (1X)" if h_pos >= a_pos else "2 (X2)"

    # Warnings
    if (real_1 + real_2) < 0.40:
        warning_msg = "⚠️ HIGH RISK MATCH: Statistics are very low, abstention is recommended."
        mode_label += " (Low Confidence)"
    if ace_odds <= 1.50 and real_X > 0.25:
        warning_msg = "⚠️ TRAP στο Χ: Ένδειξη ότι το φαβορί θα δυσκολευτεί."

confidence = max(5, min(100, int((1 - abs(real_1 - prob_1) - abs(real_2 - prob_2)) * 100)))
color = "#2ecc71" if confidence >= 80 else "#f1c40f" if confidence >= 60 else "#e74c3c"

# ==============================
# DISPLAY
# ==============================
st.markdown(f"""
<div class="sticky-result">
<div class="result-card">
<div class="mode-label" style="font-size: 0.85rem; font-weight:bold; margin-bottom: 5px;">{mode_label}</div>
<div class="proposal-text" style="font-size: 3.8rem; font-weight: 900; line-height: 1; margin: 0;">{proposal}</div>
<div style="font-size: 1.8rem; font-weight: 900; color: {color}; margin-bottom: 15px;">{confidence}%</div>
<div style="max-width: 550px; margin: 0 auto;">
<div style="width: 100%; height: 32px; background: rgba(128,128,128,0.2); position: relative; border-radius: 16px; border: 1px solid rgba(128,128,128,0.3); overflow: hidden;">
<div style="width: {confidence}%; background: {color}; height: 100%; transition: width 0.8s;"></div>
<div style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; display: flex; align-items: center; justify-content: center;">
<span style="color: white; font-weight: 900; font-size: 0.95rem; text-shadow: 1px 1px 2px rgba(0,0,0,0.8);">CONFIDENCE BAR</span>
</div></div></div></div></div>
""", unsafe_allow_html=True)

if warning_msg: st.markdown(f'<div class="warning-box">{warning_msg}</div>', unsafe_allow_html=True)

st.markdown("### 📝 Στατιστικά Ομάδων")
c1, c2 = st.columns(2)
with c1:
    st.markdown(f'**🏠 Γηπεδούχος** <span class="pos-badge">{h_pos*100:.1f}% Positive Percentage</span>', unsafe_allow_html=True)
    st.number_input("Εντός_Νίκες", 0, 100, key="hw")
    st.number_input("Εντός_Ισοπαλίες", 0, 100, key="hd")
    st.number_input("Εντός_Ήττες", 0, 100, key="hl")
with c2:
    st.markdown(f'**🚀 Φιλοξενούμενος** <span class="pos-badge">{a_pos*100:.1f}% Positive Percentage</span>', unsafe_allow_html=True)
    st.number_input("Εκτός_Νίκες (A)", 0, 100, key="aw")
    st.number_input("Εκτός_Ισοπαλίες (A)", 0, 100, key="ad")
    st.number_input("Εκτός_Ήττες (A)", 0, 100, key="al")

tab1, tab2 = st.tabs(["📊 Ανάλυση & Γράφημα", "🛡️ Οδηγός Στρατηγικής"])
with tab1:
    fig = go.Figure()
    cats = ["1", "X", "2"]
    fig.add_trace(go.Bar(name='Booker_Odds', x=cats, y=[prob_1*100, prob_X*100, prob_2*100], marker_color='#FF4B4B'))
    fig.add_trace(go.Bar(name='Performance_Stats', x=cats, y=[real_1*100, real_X*100, real_2*100], marker_color='#0083B0'))
    fig.update_layout(barmode='group', height=350, margin=dict(l=10, r=10, t=30, b=10), xaxis=dict(type='category'))
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.markdown("""
    <div style="background: rgba(255, 255, 255, 0.05); padding: 15px; border-radius: 10px; border: 1px solid rgba(128,128,128,0.2);">
        <strong style="color: #2ecc71;">Confidence >80%:</strong> Κύρια Επιλογή.<br>
        <strong style="color: #f1c40f;">Confidence 61-79%:</strong> Επιλογή για κάλυψη.<br>
        <strong style="color: #e74c3c;">Confidence <=60%:</strong> Υψηλό ρίσκο.
    </div>
    """, unsafe_allow_html=True)
