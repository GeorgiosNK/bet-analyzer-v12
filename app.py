import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import streamlit.components.v1 as components

# ==============================
# CONFIG & BASIC STYLING
# ==============================
st.set_page_config(page_title="Bet Analyzer v12.16.0", page_icon="⚽", layout="centered")

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
    .result-card {
        background-color: #0e1117;
        border: 2px solid #3498db;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
        margin-bottom: 20px;
    }
    .proposal-text { color: #ffffff; font-size: 3rem; font-weight: bold; }
    .pos-badge {
        background: #1e3c72; color: white; padding: 2px 8px; 
        border-radius: 5px; font-size: 0.8rem; float: right;
    }
</style>
""", unsafe_allow_html=True)

# ==============================
# DATA & SESSION STATE
# ==============================
if 'hw' not in st.session_state: st.session_state.update({'hw':0, 'hd':0, 'hl':0, 'aw':0, 'ad':0, 'al':0})
if 'o1_s' not in st.session_state: st.session_state.update({'o1_s': "1.00", 'ox_s': "1.00", 'o2_s': "1.00"})

def reset():
    for k in ['hw','hd','hl','aw','ad','al']: st.session_state[k] = 0
    st.session_state.o1_s, st.session_state.ox_s, st.session_state.o2_s = "1.00", "1.00", "1.00"

with st.sidebar:
    st.title("⚽ Bet Analyzer")
    st.button("🧹 Clear All Data", on_click=reset, use_container_width=True)
    o1_v = st.text_input("Άσος (1)", key="o1_s")
    ox_v = st.text_input("Ισοπαλία (X)", key="ox_s")
    o2_v = st.text_input("Διπλό (2)", key="o2_s")

def f(v):
    try: return float(str(v).replace(',', '.'))
    except: return 1.0

o1, ox, o2 = max(1.0, f(o1_v)), max(1.0, f(ox_v)), max(1.0, f(o2_v))
h_t = st.session_state.hw + st.session_state.hd + st.session_state.hl
a_t = st.session_state.aw + st.session_state.ad + st.session_state.al

inv = (1/o1 + 1/ox + 1/o2)
p1, pX, p2 = (1/o1)/inv, (1/ox)/inv, (1/o2)/inv

h_pos = (st.session_state.hw + st.session_state.hd)/h_t if h_t > 0 else 0
a_pos = (st.session_state.aw + st.session_state.ad)/a_t if a_t > 0 else 0

# Logic [cite: 2026-01-10, 2026-01-09, 2026-01-08]
warn, prop = "", ""
if (h_t + a_t) == 0:
    r1, rX, r2 = p1, pX, p2
    prop = "1 (1X)" if p1 >= p2 else "2 (X2)"
else:
    raw1, raw2 = st.session_state.hw/h_t if h_t > 0 else 0, st.session_state.aw/a_t if a_t > 0 else 0
    rawX = ((st.session_state.hd/h_t if h_t > 0 else 0) + (st.session_state.ad/a_t if a_t > 0 else 0)) / 2
    sum_r = raw1 + rawX + raw2
    r1, rX, r2 = (raw1/sum_r, rawX/sum_r, raw2/sum_r) if sum_r > 0 else (0,0,0)
    
    if rX >= 0.40: prop = "X (X2)" if a_pos >= 2 * h_pos and a_pos > 0 else "X (1X)"
    elif rX < 0.15: prop = f"{'1' if r1 >= r2 else '2'} (1-2)"
    elif r1 > 0.45 and r2 > 0.45: prop = "1 (1-2)"
    elif a_pos >= 2 * h_pos and a_pos > 0: prop = "2 (X2)"
    elif h_pos >= 2 * a_pos and h_pos > 0: prop = "1 (1X)"
    else: prop = "1 (1X)" if h_pos >= a_pos else "2 (X2)"

    if (r1 + r2) < 0.40: warn = "⚠️ HIGH RISK MATCH: Statistics are very low."
    if o1 <= 1.50 and rX > 0.25: warn = "⚠️ TRAP στο Χ: Ένδειξη δυσκολίας του φαβορί."

conf = max(5, min(100, int((1 - abs(r1 - p1) - abs(r2 - p2)) * 100)))

# ==============================
# DISPLAY
# ==============================
st.markdown(f"""
<div class="result-card">
    <div style="color: #3498db; font-weight: bold;">ΠΡΟΤΑΣΗ</div>
    <div class="proposal-text">{prop}</div>
    <div style="font-size: 1.5rem; color: #2ecc71;">{conf}% Confidence</div>
</div>
""", unsafe_allow_html=True)

if warn: st.warning(warn)

col1, col2 = st.columns(2)
with col1:
    st.markdown(f"**🏠 Γηπεδούχος** <span class='pos-badge'>{h_pos*100:.1f}% Pos</span>", unsafe_allow_html=True)
    st.number_input("Νίκες", 0, 100, key="hw")
    st.number_input("Ισοπαλίες", 0, 100, key="hd")
    st.number_input("Ήττες", 0, 100, key="hl")
with col2:
    st.markdown(f"**🚀 Φιλοξενούμενος** <span class='pos-badge'>{a_pos*100:.1f}% Pos</span>", unsafe_allow_html=True)
    st.number_input("Νίκες ", 0, 100, key="aw")
    st.number_input("Ισοπαλίες ", 0, 100, key="ad")
    st.number_input("Ήττες ", 0, 100, key="al")

tab1, tab2 = st.tabs(["📊 Γράφημα", "🛡️ Οδηγός"])
with tab1:
    fig = go.Figure()
    # ΕΔΩ ΕΙΝΑΙ ΤΑ ΝΟΥΜΕΡΑ ΜΕΣΑ ΣΤΙΣ ΜΠΑΡΕΣ
    fig.add_trace(go.Bar(
        name='Booker %', x=["1", "X", "2"], y=[p1*100, pX*100, p2*100], 
        marker_color='#ef4444', text=[f"{p1*100:.1f}%", f"{pX*100:.1f}%", f"{p2*100:.1f}%"],
        textposition='inside', insidetextfont=dict(color='white')
    ))
    fig.add_trace(go.Bar(
        name='Real %', x=["1", "X", "2"], y=[r1*100, rX*100, r2*100], 
        marker_color='#3498db', text=[f"{r1*100:.1f}%", f"{rX*100:.1f}%", f"{r2*100:.1f}%"],
        textposition='inside', insidetextfont=dict(color='white')
    ))
    fig.update_layout(barmode='group', height=300, template="plotly_white", margin=dict(l=20, r=20, t=20, b=20))
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.info("Οδηγός: Confidence >80% = Κύρια Επιλογή. Positive Percentage = Νίκες + Ισοπαλίες.")
