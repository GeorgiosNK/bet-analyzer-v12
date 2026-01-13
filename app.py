import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import streamlit.components.v1 as components

# ==============================
# CONFIG & PROFESSIONAL UI FIX
# ==============================
st.set_page_config(page_title="Bet Analyzer v12.15.2 FINAL", page_icon="⚽", layout="centered")

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
    /* Sticky Card Logic */
    [data-testid="stVerticalBlock"] > div:has(div.sticky-result) {
        position: sticky; top: 2.8rem; z-index: 1000;
        background: transparent; padding-bottom: 10px;
    }
    
    /* CLEANER CARD - Adaptive to Theme */
    .result-card {
        background-color: #1a1c23 !important;
        border: 2px solid #3498db !important;
        border-radius: 12px;
        padding: 25px;
        text-align: center;
        margin-bottom: 20px;
        box-shadow: 0 8px 16px rgba(0,0,0,0.3);
    }
    
    .mode-label { color: #3498db !important; font-size: 0.85rem; font-weight: bold; letter-spacing: 1px; }
    .proposal-text { color: #ffffff !important; font-size: 3.5rem; font-weight: 900; line-height: 1; margin: 10px 0; }
    
    /* FIXED TEAM HEADERS */
    .team-container {
        display: flex; justify-content: space-between; align-items: center;
        margin-bottom: 15px; padding-bottom: 5px; border-bottom: 2px solid #3498db;
    }
    
    .team-title { font-size: 1.1rem; font-weight: bold; }
    
    .pos-badge {
        background: #3498db; color: white; padding: 2px 10px; 
        border-radius: 6px; font-size: 0.8rem; font-weight: bold;
    }

    .guide-box {
        background: rgba(52, 152, 219, 0.05); border-radius: 8px; padding: 12px;
        margin: 8px 0; border-left: 4px solid #3498db; font-size: 0.9rem;
    }
    
    /* Input Alignment Fix */
    div[data-testid="stNumberInput"] label { font-weight: bold !important; color: inherit !important; }
</style>
""", unsafe_allow_html=True)

# ==============================
# LOGIC ENGINE
# ==============================
if 'hw' not in st.session_state: st.session_state.update({'hw':0, 'hd':0, 'hl':0, 'aw':0, 'ad':0, 'al':0})
if 'o1_s' not in st.session_state: st.session_state.update({'o1_s': "1.00", 'ox_s': "1.00", 'o2_s': "1.00"})

def reset():
    for k in ['hw','hd','hl','aw','ad','al']: st.session_state[k] = 0
    st.session_state.o1_s, st.session_state.ox_s, st.session_state.o2_s = "1.00", "1.00", "1.00"

with st.sidebar:
    st.title("⚽ Analyzer Pro")
    st.button("🧹 Reset Data", on_click=reset, use_container_width=True)
    o1_in = st.text_input("Άσος (1)", key="o1_s")
    ox_in = st.text_input("Ισοπαλία (X)", key="ox_s")
    o2_in = st.text_input("Διπλό (2)", key="o2_s")

def f(v):
    try: return float(str(v).replace(',', '.'))
    except: return 1.0

o1, ox, o2 = max(1.0, f(o1_in)), max(1.0, f(ox_in)), max(1.0, f(o2_in))
h_t = st.session_state.hw + st.session_state.hd + st.session_state.hl
a_t = st.session_state.aw + st.session_state.ad + st.session_state.al

inv = (1/o1 + 1/ox + 1/o2)
p1, pX, p2 = (1/o1)/inv, (1/ox)/inv, (1/o2)/inv

h_pos = (st.session_state.hw + st.session_state.hd)/h_t if h_t > 0 else 0
a_pos = (st.session_state.aw + st.session_state.ad)/a_t if a_t > 0 else 0

warn, prop, mode = "", "", ""

if (h_t + a_t) == 0:
    r1, rX, r2 = p1, pX, p2
    mode, prop = "⚖️ BLIND MODE • ΠΡΟΤΑΣΗ", ("1 (1X)" if p1 >= p2 else "2 (X2)")
else:
    raw1, raw2 = st.session_state.hw/h_t if h_t > 0 else 0, st.session_state.aw/a_t if a_t > 0 else 0
    rawX = ((st.session_state.hd/h_t if h_t > 0 else 0) + (st.session_state.ad/a_t if a_t > 0 else 0)) / 2
    sum_r = raw1 + rawX + raw2
    r1, rX, r2 = (raw1/sum_r, rawX/sum_r, raw2/sum_r) if sum_r > 0 else (0,0,0)
    mode = "⚖️ ΣΤΑΤΙΣΤΙΚΗ ΥΠΕΡΟΧΗ • ΠΡΟΤΑΣΗ"
    
    # [cite: 2026-01-10, 2026-01-09]
    if rX >= 0.40: prop = "X (X2)" if a_pos >= 2 * h_pos and a_pos > 0 else "X (1X)"
    elif rX < 0.15: prop = f"{'1' if r1 >= r2 else '2'} (1-2)"
    elif r1 > 0.45 and r2 > 0.45: prop = "1 (1-2)"
    elif a_pos >= 2 * h_pos and a_pos > 0: prop = "2 (X2)"
    elif h_pos >= 2 * a_pos and h_pos > 0: prop = "1 (1X)"
    else: prop = "1 (1X)" if h_pos >= a_pos else "2 (X2)"

    if (r1 + r2) < 0.40: warn = "⚠️ HIGH RISK MATCH: Statistics are very low, abstention is recommended." [cite: 2026-01-08]
    if o1 <= 1.50 and rX > 0.25: warn = "⚠️ TRAP στο Χ: Ένδειξη ότι το φαβορί θα δυσκολευτεί." [cite: 2026-01-08]

conf = max(5, min(100, int((1 - abs(r1 - p1) - abs(r2 - p2)) * 100)))
c_clr = "#2ecc71" if conf >= 80 else "#f1c40f" if conf >= 60 else "#e74c3c"

# ==============================
# UI RENDERING
# ==============================
st.markdown(f"""
<div class="sticky-result">
<div class="result-card">
    <div class="mode-label">{mode}</div>
    <div class="proposal-text">{prop}</div>
    <div style="font-size: 1.8rem; font-weight: 900; color: {c_clr};">{conf}% Confidence</div>
    <div style="width: 100%; height: 10px; background: #2d3436; border-radius: 5px; margin-top: 15px; overflow: hidden;">
        <div style="width: {conf}%; background: {c_clr}; height: 100%;"></div>
    </div>
</div></div>
""", unsafe_allow_html=True)

if warn: st.error(warn)

st.markdown("### 📝 Στατιστικά Ομάδων")
col1, col2 = st.columns(2)

with col1:
    st.markdown(f'<div class="team-container"><span class="team-title">🏠 Γηπεδούχος</span><span class="pos-badge">{h_pos*100:.1f}% Pos</span></div>', unsafe_allow_html=True)
    st.number_input("Νίκες", 0, 100, key="hw")
    st.number_input("Ισοπαλίες", 0, 100, key="hd")
    st.number_input("Ήττες", 0, 100, key="hl")

with col2:
    st.markdown(f'<div class="team-container"><span class="team-title">🚀 Φιλοξενούμενος</span><span class="pos-badge">{a_pos*100:.1f}% Pos</span></div>', unsafe_allow_html=True)
    st.number_input("Νίκες ", 0, 100, key="aw")
    st.number_input("Ισοπαλίες ", 0, 100, key="ad")
    st.number_input("Ήττες ", 0, 100, key="al")

t1, t2 = st.tabs(["📊 Ανάλυση & Γράφημα", "🛡️ Οδηγός Στρατηγικής"])

with t1:
    fig = go.Figure()
    fig.add_trace(go.Bar(
        name='Booker Odds (%)', x=["1", "X", "2"], y=[p1*100, pX*100, p2*100], 
        marker_color='#e74c3c', text=[f"{p1*100:.1f}%" for _ in range(3)], textposition='inside',
        insidetextfont=dict(color='white')
    ))
    fig.data[0].text = [f"{p1*100:.1f}%", f"{pX*100:.1f}%", f"{p2*100:.1f}%"]
    
    fig.add_trace(go.Bar(
        name='Real Performance (%)', x=["1", "X", "2"], y=[r1*100, rX*100, r2*100], 
        marker_color='#3498db', text=[f"{r1*100:.1f}%", f"{rX*100:.1f}%", f"{r2*100:.1f}%"], textposition='inside',
        insidetextfont=dict(color='white')
    ))
    fig.update_layout(barmode='group', height=350, template="plotly_white", margin=dict(l=20, r=20, t=30, b=20), legend=dict(orientation="h", y=1.1))
    st.plotly_chart(fig, use_container_width=True)

with t2:
    # [cite: 2026-01-03, 2026-01-09]
    st.markdown("""
    <div class="guide-box"><b>Confidence >80%:</b> Κύρια Επιλογή. Μέγιστη στατιστική ασφάλεια.</div>
    <div class="guide-box"><b>Confidence 61-79%:</b> Επιλογή για κάλυψη (π.χ. Διπλή Ευκαιρία).</div>
    <div class="guide-box"><b>Confidence <=60%:</b> Υψηλό ρίσκο.</div>
    <div class="guide-box"><b>Positive Percentage (Wins + Draws):</b> Το συνολικό ποσοστό αποφυγής ήττας.</div>
    """, unsafe_allow_html=True)
