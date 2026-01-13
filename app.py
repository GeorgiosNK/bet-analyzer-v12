import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import streamlit.components.v1 as components

# ==============================
# CONFIG & PROFESSIONAL CSS
# ==============================
st.set_page_config(page_title="Bet Analyzer v12.13.2 PRO", page_icon="⚽", layout="centered")

# SMART JAVASCRIPT FIX: Auto-select & Comma-to-Dot Conversion
components.html(
    """
    <script>
        const setupInputs = () => {
            const inputs = window.parent.document.querySelectorAll('input');
            inputs.forEach(input => {
                input.addEventListener('focus', function() { this.select(); });
                input.addEventListener('input', function() {
                    if(this.value.includes(',')) {
                        this.value = this.value.replace(',', '.');
                    }
                });
            });
        }
        setTimeout(setupInputs, 1000);
        setInterval(setupInputs, 3000);
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
    .conf-bar { height: 24px; border-radius: 12px; background: #f0f2f6; overflow: hidden; position: relative; border: 1px solid #ddd; }
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
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="info-text">
    <strong>⚽ Bet Analyzer Pro v12.13.2</strong><br>
    Ο Bet Analyzer συνδυάζει Market Odds με Real Stats.
</div>
""", unsafe_allow_html=True)

# ==============================
# INITIALIZATION & RESET
# ==============================
if 'hw' not in st.session_state:
    st.session_state.update({'hw':0, 'hd':0, 'hl':0, 'aw':0, 'ad':0, 'al':0})
if 'o1_str' not in st.session_state:
    st.session_state.update({'o1_str': "1.00", 'ox_str': "1.00", 'o2_str': "1.00"})

def reset_everything():
    for k in ['hw','hd','hl','aw','ad','al']: st.session_state[k] = 0
    st.session_state.o1_str, st.session_state.ox_str, st.session_state.o2_str = "1.00", "1.00", "1.00"

# ==============================
# SIDEBAR
# ==============================
with st.sidebar:
    st.markdown("### 🏆 Bet Analyzer Pro")
    st.button("🧹 Clear All Stats & Odds", on_click=reset_everything, use_container_width=True)
    st.header("📊 Αποδόσεις (Odds)")
    o1_input = st.text_input("Άσος (1)", key="o1_str")
    ox_input = st.text_input("Ισοπαλία (X)", key="ox_str")
    o2_input = st.text_input("Διπλό (2)", key="o2_str")

def safe_float(val):
    try: return float(str(val).replace(',', '.'))
    except: return 1.00

ace_odds, draw_odds, double_odds = max(1.0, safe_float(o1_input)), max(1.0, safe_float(ox_input)), max(1.0, safe_float(o2_input))

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

if total_all == 0:
    real_1, real_X, real_2 = prob_1, prob_X, prob_2
    mode_label, proposal = "⚖️ BLIND MODE • ΠΡΟΤΑΣΗ", ("1 (1X)" if prob_1 >= prob_2 else "2 (X2)")
else:
    real_1, real_X, real_2 = st.session_state.hw/h_total if h_total > 0 else 0, (st.session_state.hd + st.session_state.ad)/total_all if total_all > 0 else 0, st.session_state.aw/a_total if a_total > 0 else 0
    mode_label = "⚖️ ΣΤΑΤΙΣΤΙΚΗ ΥΠΕΡΟΧΗ • ΠΡΟΤΑΣΗ"
    if real_X >= 0.40: proposal = "X (X2)" if a_pos >= 2 * h_pos and a_pos > 0 else "X (1X)"
    elif real_X < 0.15: proposal = f"{'1' if real_1 >= real_2 else '2'} (1-2)"
    elif real_1 > 0.45 and real_2 > 0.45: proposal = "1 (1-2)"
    elif a_pos >= 2 * h_pos and a_pos > 0: proposal = "2 (X2)"
    elif h_pos >= 2 * a_pos and h_pos > 0: proposal = "1 (1X)"
    else: proposal = "1 (1X)" if h_pos >= a_pos else "2 (X2)"

confidence = max(5, min(100, int((1 - abs(real_1 - prob_1) - abs(real_2 - prob_2)) * 100)))
color = "#2ecc71" if confidence >= 80 else "#f1c40f" if confidence >= 60 else "#e74c3c"

# ==============================
# RESULTS & INPUTS
# ==============================
st.markdown(f"""
<div class="sticky-result">
<div class="result-card">
<div style="font-size: 0.75rem; color: #666; font-weight:bold;">{mode_label}</div>
<div style="font-size: 3.5rem; font-weight: 900; color: #1e3c72; line-height: 1;">{proposal}</div>
<div style="font-size: 1.6rem; font-weight: 900; color: {color};">{confidence}%</div>
<div style="max-width: 550px; margin: 10px auto 0;">
<div style="width: 100%; height: 32px; background: #f0f2f6; position: relative; border-radius: 16px; border: 1px solid #ddd; overflow: hidden;">
<div style="width: {confidence}%; background: {color}; height: 100%;"></div>
</div></div></div></div>
""", unsafe_allow_html=True)

c1, c2 = st.columns(2)
with c1:
    st.markdown(f'**🏠 Γηπεδούχος** <span class="pos-badge">{h_pos*100:.1f}% Pos</span>', unsafe_allow_html=True)
    st.number_input("Εντός_Νίκες", 0, 100, key="hw")
    st.number_input("Εντός_Ισοπαλίες", 0, 100, key="hd")
    st.number_input("Εντός_Ήττες", 0, 100, key="hl")
with c2:
    st.markdown(f'**🚀 Φιλοξενούμενος** <span class="pos-badge">{a_pos*100:.1f}% Pos</span>', unsafe_allow_html=True)
    st.number_input("Εκτός_Νίκες (A)", 0, 100, key="aw")
    st.number_input("Εκτός_Ισοπαλίες (A)", 0, 100, key="ad")
    st.number_input("Εκτός_Ήττες (A)", 0, 100, key="al")

# ==============================
# GRAPH WITH BOLD WHITE LABELS
# ==============================
tab1, tab2 = st.tabs(["📊 Γράφημα", "🛡️ Οδηγός"])
with tab1:
    fig = go.Figure()
    x_labels = ["1", "X", "2"]
    # Booker Bar
    fig.add_trace(go.Bar(
        name='Booker %', x=x_labels, y=[prob_1*100, prob_X*100, prob_2*100], 
        marker_color='#FF4B4B', 
        text=[f"<b>{prob_1*100:.1f}%</b>", f"<b>{prob_X*100:.1f}%</b>", f"<b>{prob_2*100:.1f}%</b>"], 
        textposition='inside', insidetextfont=dict(color='white', size=14)
    ))
    # Real Bar
    fig.add_trace(go.Bar(
        name='Real %', x=x_labels, y=[real_1*100, real_X*100, real_2*100], 
        marker_color='#0083B0', 
        text=[f"<b>{real_1*100:.1f}%</b>", f"<b>{real_X*100:.1f}%</b>", f"<b>{real_2*100:.1f}%</b>"], 
        textposition='inside', insidetextfont=dict(color='white', size=14)
    ))
    fig.update_layout(barmode='group', height=350, margin=dict(l=10, r=10, t=10, b=10), xaxis=dict(type='category'))
    st.plotly_chart(fig, use_container_width=True)
