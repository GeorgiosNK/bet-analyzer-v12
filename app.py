import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import streamlit.components.v1 as components

# ==============================
# CONFIG & ULTIMATE THEME FIX
# ==============================
st.set_page_config(page_title="Bet Analyzer v12.14.9 MASTER FINAL", page_icon="⚽", layout="centered")

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
    /* Sticky Header */
    [data-testid="stVerticalBlock"] > div:has(div.sticky-result) {
        position: sticky; top: 2.8rem; z-index: 1000;
        background: transparent; padding-bottom: 10px;
    }
    
    /* HARDLOCKED DARK CARD - Works in both Light & Dark Mode */
    .result-card {
        background-color: #111827 !important; /* Deep Navy Black */
        border: 2px solid #3b82f6 !important; /* Bright Blue Border */
        border-radius: 15px;
        padding: 1.5rem;
        text-align: center;
        margin-bottom: 15px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.5);
    }
    
    .mode-label { color: #60a5fa !important; font-size: 0.85rem; font-weight: bold; margin-bottom: 5px; }
    .proposal-text { color: #ffffff !important; font-size: 3.8rem; font-weight: 900; line-height: 1; margin: 0; }
    
    /* Force Strategy Guide to be visible */
    .guide-item { 
        padding: 15px; margin: 10px 0; border-radius: 8px; font-size: 0.9rem;
        background: #1f2937 !important; /* Dark Grey background */
        color: #f3f4f6 !important; /* Off-white text */
        border: 1px solid #374151;
    }

    .pos-badge {
        background: #1e3c72; color: white; padding: 3px 10px; 
        border-radius: 5px; font-size: 0.85rem; margin-left: 10px; font-weight: bold;
    }

    .warning-box {
        background-color: rgba(231, 76, 60, 0.2); color: #ff6b6b; padding: 12px; 
        border-radius: 8px; border: 1px solid #e74c3c; margin-top: 10px; 
        font-weight: bold; text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# ==============================
# DATA ENGINE
# ==============================
if 'hw' not in st.session_state: st.session_state.update({'hw':0, 'hd':0, 'hl':0, 'aw':0, 'ad':0, 'al':0})
if 'o1_str' not in st.session_state: st.session_state.update({'o1_str': "1.00", 'ox_str': "1.00", 'o2_str': "1.00"})

def reset_everything():
    for k in ['hw','hd','hl','aw','ad','al']: st.session_state[k] = 0
    st.session_state.o1_str = "1.00"; st.session_state.ox_str = "1.00"; st.session_state.o2_str = "1.00"

with st.sidebar:
    st.markdown("### 🏆 Bet Analyzer Pro")
    st.caption("Version 12.14.9 FINAL")
    st.divider()
    st.button("🧹 Clear All Stats", on_click=reset_everything, use_container_width=True)
    o1_txt = st.text_input("Άσος (1)", key="o1_str")
    ox_txt = st.text_input("Ισοπαλία (X)", key="ox_str")
    o2_txt = st.text_input("Διπλό (2)", key="o2_str")

def safe_float(val):
    try: return float(str(val).replace(',', '.'))
    except: return 1.00

ace_odds = max(1.0, safe_float(o1_txt))
draw_odds = max(1.0, safe_float(ox_txt))
double_odds = max(1.0, safe_float(o2_txt))

# Logic Calculation
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
    
    # [cite: 2026-01-10, 2026-01-09]
    if real_X >= 0.40: proposal = "X (X2)" if a_pos >= 2 * h_pos and a_pos > 0 else "X (1X)"
    elif real_X < 0.15: proposal = f"{'1' if real_1 >= real_2 else '2'} (1-2)"
    elif real_1 > 0.45 and real_2 > 0.45: proposal = "1 (1-2)"
    elif a_pos >= 2 * h_pos and a_pos > 0: proposal = "2 (X2)"
    elif h_pos >= 2 * a_pos and h_pos > 0: proposal = "1 (1X)"
    else: proposal = "1 (1X)" if h_pos >= a_pos else "2 (X2)"

    if (real_1 + real_2) < 0.40: # [cite: 2026-01-08]
        warning_msg = "⚠️ HIGH RISK MATCH: Statistics are very low, abstention is recommended."
    if ace_odds <= 1.50 and real_X > 0.25: # [cite: 2026-01-08]
        warning_msg = "⚠️ TRAP στο Χ: Ένδειξη ότι το φαβορί θα δυσκολευτεί."

confidence = max(5, min(100, int((1 - abs(real_1 - prob_1) - abs(real_2 - prob_2)) * 100)))
color = "#2ecc71" if confidence >= 80 else "#f1c40f" if confidence >= 60 else "#e74c3c"

# ==============================
# UI RENDERING
# ==============================
st.markdown(f"""
<div class="sticky-result">
<div class="result-card">
<div class="mode-label">{mode_label}</div>
<div class="proposal-text">{proposal}</div>
<div style="font-size: 1.8rem; font-weight: 900; color: {color}; margin-bottom: 15px;">{confidence}%</div>
<div style="max-width: 550px; margin: 0 auto;">
<div style="width: 100%; height: 32px; background: rgba(255,255,255,0.1); position: relative; border-radius: 16px; border: 1px solid rgba(255,255,255,0.2); overflow: hidden;">
<div style="width: {confidence}%; background: {color}; height: 100%;"></div>
<div style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; display: flex; align-items: center; justify-content: center;">
<span style="color: white; font-weight: 900; font-size: 0.9rem;">CONFIDENCE BAR</span>
</div></div></div></div></div>
""", unsafe_allow_html=True)

if warning_msg: st.markdown(f'<div class="warning-box">{warning_msg}</div>', unsafe_allow_html=True)

st.markdown("### 📝 Στατιστικά Ομάδων")
c1, c2 = st.columns(2)
with c1:
    # [cite: 2026-01-09]
    st.markdown(f'**🏠 Γηπεδούχος** <span class="pos-badge">{h_pos*100:.1f}% Positive Percentage (Wins + Draws)</span>', unsafe_allow_html=True)
    st.number_input("Εντός_Νίκες", 0, 100, key="hw")
    st.number_input("Εντός_Ισοπαλίες", 0, 100, key="hd")
    st.number_input("Εντός_Ήττες", 0, 100, key="hl")
with c2:
    st.markdown(f'**🚀 Φιλοξενούμενος** <span class="pos-badge">{a_pos*100:.1f}% Positive Percentage (Wins + Draws)</span>', unsafe_allow_html=True)
    st.number_input("Εκτός_Νίκες (A)", 0, 100, key="aw")
    st.number_input("Εκτός_Ισοπαλίες (A)", 0, 100, key="ad")
    st.number_input("Εκτός_Ήττες (A)", 0, 100, key="al")

tab1, tab2 = st.tabs(["📊 Ανάλυση & Γράφημα", "🛡️ Οδηγός Στρατηγικής"])

with tab1:
    fig = go.Figure()
    cats = ["1", "X", "2"]
    fig.add_trace(go.Bar(name='Booker Odds (%)', x=cats, y=[prob_1*100, prob_X*100, prob_2*100], marker_color='#ef4444'))
    fig.add_trace(go.Bar(name='Real Performance (%)', x=cats, y=[real_1*100, real_X*100, real_2*100], marker_color='#3b82f6'))
    fig.update_layout(barmode='group', height=350, margin=dict(l=10, r=10, t=30, b=10), template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.markdown("""
    <div class="guide-item" style="border-left: 5px solid #2ecc71;">
        <strong style="color: #2ecc71;">Confidence >80% (Πράσινο):</strong> Κύρια Επιλογή. Μέγιστη στατιστική ασφάλεια.
    </div>
    <div class="guide-item" style="border-left: 5px solid #f1c40f;">
        <strong style="color: #f1c40f;">Confidence 61-79% (Κίτρινο):</strong> Επιλογή για κάλυψη ή μικρότερο ποντάρισμα.
    </div>
    <div class="guide-item" style="border-left: 5px solid #e74c3c;">
        <strong style="color: #e74c3c;">Confidence <=60% (Κόκκινο):</strong> Υψηλό ρίσκο/Τζόγος.
    </div>
    """, unsafe_allow_html=True)
