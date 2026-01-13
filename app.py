import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import streamlit.components.v1 as components

# ==============================
# CONFIG & CLEAN UI
# ==============================
st.set_page_config(page_title="Bet Analyzer v12.15.1 FINAL", page_icon="⚽", layout="centered")

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
    [data-testid="stVerticalBlock"] > div:has(div.sticky-result) {
        position: sticky; top: 2.8rem; z-index: 1000;
        background: transparent; padding-bottom: 10px;
    }
    
    .result-card {
        background-color: #0e1117 !important;
        border: 2px solid #3498db !important;
        border-radius: 15px;
        padding: 20px;
        text-align: center;
        margin-bottom: 20px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.5);
    }
    
    .mode-label { color: #3498db !important; font-size: 0.9rem; font-weight: bold; text-transform: uppercase; }
    .proposal-text { color: #ffffff !important; font-size: 3.5rem; font-weight: 900; line-height: 1.2; }
    
    .team-header {
        display: flex; align-items: center; justify-content: space-between;
        margin-bottom: 10px; padding: 5px 0; border-bottom: 1px solid #31333f;
    }

    .pos-badge {
        background: #1e3c72; color: white; padding: 4px 12px; 
        border-radius: 20px; font-size: 0.75rem; font-weight: bold;
    }

    .guide-box {
        background: #161b22; border-radius: 10px; padding: 15px;
        margin: 10px 0; border-left: 5px solid #3498db;
    }
    
    .warning-box {
        background-color: rgba(231, 76, 60, 0.2); color: #ff4b4b; padding: 15px; 
        border-radius: 10px; border: 1px solid #ff4b4b; font-weight: bold; text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# ==============================
# LOGIC & SESSION STATE
# ==============================
if 'hw' not in st.session_state: st.session_state.update({'hw':0, 'hd':0, 'hl':0, 'aw':0, 'ad':0, 'al':0})
if 'o1_str' not in st.session_state: st.session_state.update({'o1_str': "1.00", 'ox_str': "1.00", 'o2_str': "1.00"})

def reset_all():
    for k in ['hw','hd','hl','aw','ad','al']: st.session_state[k] = 0
    st.session_state.o1_str = "1.00"; st.session_state.ox_str = "1.00"; st.session_state.o2_str = "1.00"

with st.sidebar:
    st.title("🏆 Bet Analyzer Pro")
    st.button("🧹 Clear All Stats", on_click=reset_all, use_container_width=True)
    o1_v = st.text_input("Άσος (1)", key="o1_str")
    ox_v = st.text_input("Ισοπαλία (X)", key="ox_str")
    o2_v = st.text_input("Διπλό (2)", key="o2_str")

def to_f(val):
    try: return float(str(val).replace(',', '.'))
    except: return 1.0

o1, ox, o2 = max(1.0, to_f(o1_v)), max(1.0, to_f(ox_v)), max(1.0, to_f(o2_v))

h_t = st.session_state.hw + st.session_state.hd + st.session_state.hl
a_t = st.session_state.aw + st.session_state.ad + st.session_state.al
total = h_t + a_t

inv = (1/o1 + 1/ox + 1/o2)
p1, pX, p2 = (1/o1)/inv, (1/ox)/inv, (1/o2)/inv

h_pos = (st.session_state.hw + st.session_state.hd)/h_t if h_t > 0 else 0
a_pos = (st.session_state.aw + st.session_state.ad)/a_t if a_t > 0 else 0

warn, prop, mode = "", "", ""

if total == 0:
    r1, rX, r2 = p1, pX, p2
    mode, prop = "⚖️ BLIND MODE • ΠΡΟΤΑΣΗ", ("1 (1X)" if p1 >= p2 else "2 (X2)")
else:
    raw1, raw2 = st.session_state.hw/h_t if h_t > 0 else 0, st.session_state.aw/a_t if a_t > 0 else 0
    rawX = ((st.session_state.hd/h_t if h_t > 0 else 0) + (st.session_state.ad/a_t if a_t > 0 else 0)) / 2
    sum_r = raw1 + rawX + raw2
    r1, rX, r2 = (raw1/sum_r, rawX/sum_r, raw2/sum_r) if sum_r > 0 else (0,0,0)
    mode = "⚖️ ΣΤΑΤΙΣΤΙΚΗ ΥΠΕΡΟΧΗ"
    
    if rX >= 0.40: prop = "X (X2)" if a_pos >= 2 * h_pos and a_pos > 0 else "X (1X)"
    elif rX < 0.15: prop = f"{'1' if r1 >= r2 else '2'} (1-2)"
    elif r1 > 0.45 and r2 > 0.45: prop = "1 (1-2)"
    elif a_pos >= 2 * h_pos and a_pos > 0: prop = "2 (X2)"
    elif h_pos >= 2 * a_pos and h_pos > 0: prop = "1 (1X)"
    else: prop = "1 (1X)" if h_pos >= a_pos else "2 (X2)"

    if (r1 + r2) < 0.40: warn = "⚠️ HIGH RISK MATCH: Statistics are very low, abstention is recommended."
    if o1 <= 1.50 and rX > 0.25: warn = "⚠️ TRAP στο Χ: Ένδειξη ότι το φαβορί θα δυσκολευτεί."

conf = max(5, min(100, int((1 - abs(r1 - p1) - abs(r2 - p2)) * 100)))
c_clr = "#2ecc71" if conf >= 80 else "#f1c40f" if conf >= 60 else "#e74c3c"

# ==============================
# DISPLAY RENDERING
# ==============================
st.markdown(f"""
<div class="sticky-result">
<div class="result-card">
    <div class="mode-label">{mode}</div>
    <div class="proposal-text">{prop}</div>
    <div style="font-size: 2rem; font-weight: 900; color: {c_clr};">{conf}%</div>
    <div style="width: 100%; height: 12px; background: #31333f; border-radius: 6px; margin-top: 10px; overflow: hidden;">
        <div style="width: {conf}%; background: {c_clr}; height: 100%;"></div>
    </div>
</div></div>
""", unsafe_allow_html=True)

if warn: st.markdown(f'<div class="warning-box">{warn}</div>', unsafe_allow_html=True)

st.markdown("### 📝 Στατιστικά Ομάδων")
col1, col2 = st.columns(2)
with col1:
    st.markdown(f'<div class="team-header"><b>🏠 Γηπεδούχος</b> <span class="pos-badge">{h_pos*100:.1f}% Positive Percentage</span></div>', unsafe_allow_html=True)
    st.number_input("Νίκες", 0, 100, key="hw")
    st.number_input("Ισοπαλίες", 0, 100, key="hd")
    st.number_input("Ήττες", 0, 100, key="hl")
with col2:
    st.markdown(f'<div class="team-header"><b>🚀 Φιλοξενούμενος</b> <span class="pos-badge">{a_pos*100:.1f}% Positive Percentage</span></div>', unsafe_allow_html=True)
    st.number_input("Νίκες (A)", 0, 100, key="aw")
    st.number_input("Ισοπαλίες (A)", 0, 100, key="ad")
    st.number_input("Ήττες (A)", 0, 100, key="al")

t1, t2 = st.tabs(["📊 Ανάλυση & Γράφημα", "🛡️ Οδηγός Στρατηγικής"])
with t1:
    fig = go.Figure()
    # Εδώ προστέθηκαν τα text και textposition για τα νούμερα μέσα στις μπάρες
    fig.add_trace(go.Bar(
        name='Booker Odds (%)', x=["1", "X", "2"], y=[p1*100, pX*100, p2*100], 
        marker_color='#ef4444', text=[f"{p1*100:.1f}%", f"{pX*100:.1f}%", f"{p2*100:.1f}%"],
        textposition='inside', insidetextfont=dict(color='white', weight='bold')
    ))
    fig.add_trace(go.Bar(
        name='Real Performance (%)', x=["1", "X", "2"], y=[r1*100, rX*100, r2*100], 
        marker_color='#3498db', text=[f"{r1*100:.1f}%", f"{rX*100:.1f}%", f"{r2*100:.1f}%"],
        textposition='inside', insidetextfont=dict(color='white', weight='bold')
    ))
    fig.update_layout(barmode='group', height=350, template="plotly_dark", margin=dict(l=20, r=20, t=20, b=20), legend=dict(orientation="h", y=1.1))
    st.plotly_chart(fig, use_container_width=True)

with t2:
    st.markdown(f"""
    <div class="guide-box" style="border-left-color: #2ecc71;">
        <b style="color: #2ecc71;">Confidence >80% (Πράσινο):</b> Κύρια Επιλογή. Μέγιστη στατιστική ασφάλεια βασισμένη στη φόρμα των ομάδων.
    </div>
    <div class="guide-box" style="border-left-color: #f1c40f;">
        <b style="color: #f1c40f;">Confidence 61-79% (Κίτρινο):</b> Επιλογή για κάλυψη (π.χ. Διπλή Ευκαιρία) ή χαμηλότερο ποντάρισμα.
    </div>
    <div class="guide-box" style="border-left-color: #e74c3c;">
        <b style="color: #e74c3c;">Confidence <=60% (Κόκκινο):</b> Υψηλό ρίσκο. Η στατιστική αποκλίνει σημαντικά από τις αποδόσεις.
    </div>
    <div class="guide-box" style="border-left-color: #3498db;">
        <b>Positive Percentage (Wins + Draws):</b> Το ποσοστό των αγώνων που η ομάδα δεν έχασε (Νίκες + Ισοπαλίες).
    </div>
    """, unsafe_allow_html=True)
