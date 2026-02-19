import streamlit as st
import plotly.graph_objects as go
import streamlit.components.v1 as components

# ==============================
# CONFIG
# ==============================
st.set_page_config(page_title="BetAnalyzer v17.2.8 PRO", page_icon="⚽", layout="centered")

# ==============================
# JS INPUT FIX (Auto-select & Comma to Dot)
# ==============================
components.html("""
<script>
const setupInputs = () => {
    const inputs = window.parent.document.querySelectorAll('input');
    inputs.forEach(input => {
        input.addEventListener('focus', function() { this.select(); });
        input.setAttribute('inputmode', 'decimal');
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
""", height=0)

# ==============================
# PROFESSIONAL CSS
# ==============================
st.markdown("""
<style>
.result-card {
    background: #ffffff; padding: 1.5rem; border-radius: 15px;
    border: 2px solid #1e3c72; text-align: center;
    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
}
.warning-box {
    background-color: #fff3cd; color: #856404; padding: 12px; 
    border-radius: 8px; border: 1px solid #ffeeba; margin: 10px 0;
    font-weight: bold; text-align: center;
}
.dc-card {
    padding: 15px; border-radius: 10px; margin: 10px 0; 
    border-left: 5px solid;
    transition: transform 0.2s;
}
.dc-card:hover {
    transform: translateX(5px);
}
</style>
""", unsafe_allow_html=True)

# ==============================
# STATE INITIALIZATION
# ==============================
if 'hw' not in st.session_state:
    st.session_state.hw, st.session_state.hd, st.session_state.hl = 0, 0, 0
    st.session_state.aw, st.session_state.ad, st.session_state.al = 0, 0, 0

if 'o1' not in st.session_state:
    st.session_state.o1, st.session_state.ox, st.session_state.o2 = "1.00", "1.00", "1.00"

if 'current_proposal' not in st.session_state:
    st.session_state.current_proposal = ""

def reset_all():
    for key in ['hw', 'hd', 'hl', 'aw', 'ad', 'al']: st.session_state[key] = 0
    st.session_state.o1, st.session_state.ox, st.session_state.o2 = "1.00", "1.00", "1.00"
    st.session_state.current_proposal = ""

# ==============================
# ANALYSIS FUNCTIONS
# ==============================
def analyze_double_chance(p1, pX, p2, odd1, oddX, odd2, h_t, a_t, st_session):
    recommendations = []
    prob_1X, prob_X2, prob_12 = p1 + pX, pX + p2, p1 + p2
    implied_1X = 1 / (1/odd1 + 1/oddX) if odd1 > 1.0 and oddX > 1.0 else 0
    implied_X2 = 1 / (1/oddX + 1/odd2) if oddX > 1.0 and odd2 > 1.0 else 0
    implied_12 = 1 / (1/odd1 + 1/odd2) if odd1 > 1.0 and odd2 > 1.0 else 0
    
    home_losses = st_session.hl / h_t if h_t > 0 else 0.5
    away_losses = st_session.al / a_t if a_t > 0 else 0.5

    if implied_1X > 0 and prob_1X > 0.65:
        value = prob_1X - (1/implied_1X)
        if implied_1X >= 1.30:
            recommendations.append({'pick': '1X', 'prob': prob_1X * 100, 'odds': implied_1X, 'value': value * 100, 'risk': 'low' if prob_1X > 0.75 else 'medium', 'reason': f"Κάλυψη έδρας ({prob_1X*100:.0f}%)"})
    
    if implied_X2 > 0 and prob_X2 > 0.65:
        value = prob_X2 - (1/implied_X2)
        if implied_X2 >= 1.30:
            recommendations.append({'pick': 'X2', 'prob': prob_X2 * 100, 'odds': implied_X2, 'value': value * 100, 'risk': 'low' if prob_X2 > 0.75 else 'medium', 'reason': f"Κάλυψη διπλού ({prob_X2*100:.0f}%)"})

    if pX < 0.15 or (p1 > 0.45 and p2 > 0.45):
        recommendations.append({'pick': '12', 'prob': prob_12 * 100, 'odds': implied_12, 'value': (prob_12 - (1/implied_12 if implied_12 > 0 else 1)) * 100, 'risk': 'low', 'reason': "Πολύ χαμηλή πιθανότητα ισοπαλίας"})

    return recommendations

def sf(x):
    try: return max(1.01, float(str(x).replace(',','.')))
    except: return 1.01

# ==============================
# SIDEBAR & DATA
# ==============================
with st.sidebar:
    st.header("🏆 Control Panel")
    st.button("🧹 Clear Stats & Odds", on_click=reset_all, use_container_width=True)
    odd1, oddX, odd2 = sf(st.text_input("Άσος (1)", key="o1")), sf(st.text_input("Ισοπαλία (X)", key="ox")), sf(st.text_input("Διπλό (2)", key="o2"))

h_t = st.session_state.hw + st.session_state.hd + st.session_state.hl
a_t = st.session_state.aw + st.session_state.ad + st.session_state.al
total = h_t + a_t

# Probabilities Engine
try:
    inv = (1/odd1 + 1/oddX + 1/odd2)
    pm1, pmX, pm2 = (1/odd1)/inv, (1/oddX)/inv, (1/odd2)/inv
except: pm1 = pmX = pm2 = 0.33

alpha = min(1.0, total / 15) if total > 0 else 0
h_wr = (st.session_state.hw - (st.session_state.hl * 0.3)) / h_t if h_t > 0 else pm1
a_wr = (st.session_state.aw - (st.session_state.al * 0.3)) / a_t if a_t > 0 else pm2

p1, p2 = max(0.10, alpha * h_wr + (1-alpha) * pm1), max(0.10, alpha * a_wr + (1-alpha) * pm2)
pX = max(0.01, 1 - p1 - p2)

# ==============================
# CUSTOM RULES LOGIC (SAVED INFO)
# ==============================
res = max({'1': p1, 'X': pX, '2': p2}, key={'1': p1, 'X': pX, '2': p2}.get)
base = res

# 1. Κανόνας Real Stat X > 40%
if pX > 0.40:
    base = "1X" if p1 > p2 else "X2"
    if p1 > 0.40 and p2 > 0.40: base = "1X2"

# 2. Κανόνας Real Stat X < 15% ή High 1 & 2
if pX < 0.15 or (p1 > 0.45 and p2 > 0.45):
    base = "12"

# 3. Κανόνας Απόλυτης Ισορροπίας (3%)
if abs(p1 - p2) < 0.03 and pX > 0.25:
    base = "X"

# 4. Κανόνας Odds > 2.00 (Double Chance suggestion)
if (res == "1" and odd1 > 2.00) or (res == "2" and odd2 > 2.00):
    if pX < 0.70: # unless X is above 70%
        base = "1X" if res == "1" else "X2"

# 5. Αήττητο Safety
if res == "2" and st.session_state.hl == 0 and h_t >= 2: base = "1X"
elif res == "1" and st.session_state.al == 0 and a_t >= 2: base = "X2"

# Final Proposal
conf = int(max(p1, pX, p2) * 100)
proposal = f"{base} (VALUE)"
st.session_state.current_proposal = proposal

# Warning System
warning = ""
if total > 0 and (p1 + p2) < 0.40:
    warning = "⚠️ HIGH RISK MATCH: Statistics are very low, abstention is recommended."
elif odd1 <= 1.55 and pX > 0.28:
    warning = "⚠️ ΠΑΓΙΔΑ ΣΤΟ Χ: Το φαβορί δυσκολεύεται στα στατιστικά."

# ==============================
# UI OUTPUT
# ==============================
color = "#2ecc71" if conf >= 65 else "#f1c40f" if conf >= 45 else "#e74c3c"
st.markdown(f"""<div class="result-card"><div style="color:gray;font-weight:bold;margin-bottom:5px;">📊 BetAnalyzer v17.2.8 PRO</div>
<div style="font-size:3.5rem;font-weight:900;color:#1e3c72;line-height:1;">{proposal}</div>
<div style="font-size:1.8rem;font-weight:bold;color:{color};margin-top:10px;">{conf}% Confidence</div></div>""", unsafe_allow_html=True)

if warning: st.markdown(f'<div class="warning-box">{warning}</div>', unsafe_allow_html=True)

# Double Chance Section
with st.expander("🛡️ Double Chance Analysis", expanded=False):
    dc_recs = analyze_double_chance(p1, pX, p2, odd1, oddX, odd2, h_t, a_t, st.session_state)
    if dc_recs:
        for rec in dc_recs:
            st.markdown(f"""<div class="dc-card" style="background:#e3f2fd; border-left-color:#3498db;">
            <b>{rec['pick']}</b> | Prob: {rec['prob']:.1f}% | Odds: {rec['odds']:.2f} <br><small>{rec['reason']}</small></div>""", unsafe_allow_html=True)
    else: st.info("ℹ️ Δεν απαιτείται επιπλέον κάλυψη.")

# Stats Input
st.markdown("---")
c1, c2 = st.columns(2)
with c1:
    st.subheader("🏠 Γηπεδούχος")
    st.number_input("Νίκες", 0, 100, key="hw")
    st.number_input("Ισοπαλίες", 0, 100, key="hd")
    st.number_input("Ήττες", 0, 100, key="hl")
with c2:
    st.subheader("🚀 Φιλοξενούμενος")
    st.number_input("Νίκες", 0, 100, key="aw")
    st.number_input("Ισοπαλίες", 0, 100, key="ad")
    st.number_input("Ήττες", 0, 100, key="al")

# Chart
fig = go.Figure()
fig.add_trace(go.Bar(name='Bookie %', x=['1', 'X', '2'], y=[pm1*100, pmX*100, pm2*100], marker_color='#1e3c72'))
fig.add_trace(go.Bar(name='Real_Stats %', x=['1', 'X', '2'], y=[p1*100, pX*100, p2*100], marker_color='#2ecc71'))
fig.update_layout(barmode='group', height=300, margin=dict(l=20, r=20, t=20, b=20))
st.plotly_chart(fig, use_container_width=True)

st.caption(f"v17.2.8 PRO | [LIVE PROBS]: 1: {p1*100:.1f}% | X: {pX*100:.1f}% | 2: {p2*100:.1f}%")
