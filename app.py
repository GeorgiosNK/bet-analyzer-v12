import streamlit as st
import plotly.graph_objects as go
import streamlit.components.v1 as components

# ==============================
# CONFIG
# ==============================
st.set_page_config(page_title="BetAnalyzer v17.2.9", page_icon="⚽", layout="centered")

# ==============================
# JS INPUT FIX
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
}
</style>
""", unsafe_allow_html=True)

# ==============================
# STATE INITIALIZATION
# ==============================
for key in ['hw', 'hd', 'hl', 'aw', 'ad', 'al']:
    if key not in st.session_state: st.session_state[key] = 0
if 'o1' not in st.session_state: st.session_state.o1 = "1.00"
if 'ox' not in st.session_state: st.session_state.ox = "1.00"
if 'o2' not in st.session_state: st.session_state.o2 = "1.00"

def reset_all():
    for key in ['hw', 'hd', 'hl', 'aw', 'ad', 'al']: st.session_state[key] = 0
    st.session_state.o1, st.session_state.ox, st.session_state.o2 = "1.00", "1.00", "1.00"

# ==============================
# HELPER FUNCTIONS
# ==============================
def sf(x):
    try: return max(1.01, float(str(x).replace(',','.')))
    except: return 1.01

# ==============================
# SIDEBAR
# ==============================
with st.sidebar:
    st.header("🏆 Control Panel")
    st.button("🧹 Clear Stats & Odds", on_click=reset_all, use_container_width=True)
    o1_i = st.text_input("Άσος (1)", key="o1")
    ox_i = st.text_input("Ισοπαλία (X)", key="ox")
    o2_i = st.text_input("Διπλό (2)", key="o2")

odd1, oddX, odd2 = sf(o1_i), sf(ox_i), sf(o2_i)

# ==============================
# CALCULATIONS ENGINE
# ==============================
h_t = st.session_state.hw + st.session_state.hd + st.session_state.hl
a_t = st.session_state.aw + st.session_state.ad + st.session_state.al
total = h_t + a_t

inv = (1/odd1 + 1/oddX + 1/odd2)
pm1, pmX, pm2 = (1/odd1)/inv, (1/oddX)/inv, (1/odd2)/inv

alpha = min(1.0, total / 15) if total > 0 else 0
h_wr = (st.session_state.hw - (st.session_state.hl * 0.3)) / h_t if h_t > 0 else pm1
a_wr = (st.session_state.aw - (st.session_state.al * 0.3)) / a_t if a_t > 0 else pm2

p1 = alpha * h_wr + (1-alpha) * pm1
p2 = alpha * a_wr + (1-alpha) * pm2
p1, p2 = max(0.10, p1), max(0.10, p2)
pX = max(0.01, 1 - p1 - p2)

# ==============================
# FINAL LOGIC ENGINE (v17.2.9 UPDATED)
# ==============================
real_probs = {'1': p1, 'X': pX, '2': p2}
res = max(real_probs, key=real_probs.get)
conf = int(real_probs[res] * 100)
base = res
warning = ""

# --- ΕΝΣΩΜΑΤΩΣΗ ΚΑΝΟΝΩΝ ---

# 1. ΚΑΝΟΝΑΣ ΑΗΤΤΗΤΟΥ (Invincibility Rule)
home_undefeated = (st.session_state.hl == 0 and h_t >= 2)
away_undefeated = (st.session_state.al == 0 and a_t >= 2)

if res == "2" and home_undefeated:
    base = "1X"
    warning = "🛡️ Ο Γηπεδούχος είναι αήττητος. Η πρόταση άλλαξε σε 1X για ασφάλεια."
elif res == "1" and away_undefeated:
    base = "X2"
    warning = "🛡️ Ο Φιλοξενούμενος είναι αήττητος. Η πρόταση άλλαξε σε X2 για ασφάλεια."

# 2. ΚΑΝΟΝΑΣ ΑΠΟΔΟΣΗΣ > 2.00 (Double Chance Rule)
if (base == "1" and odd1 > 2.00 and pX < 0.70):
    base = "1X"
elif (base == "2" and odd2 > 2.00 and pX < 0.70):
    base = "X2"

# 3. REAL STAT X > 40% (Mandatory X)
if pX > 0.40:
    if "X" not in base:
        if base == "1": base = "1X"
        elif base == "2": base = "X2"
        else: base = "X"

# 4. ΚΑΝΟΝΑΣ ΑΠΟΛΥΤΗΣ ΙΣΟΡΡΟΠΙΑΣ (3%)
if abs(p1 - p2) < 0.03:
    base = "X"

# 5. ΚΑΝΟΝΑΣ 1-2 (High Stats)
if p1 > 0.45 and p2 > 0.45:
    base = "1-2"

# 6. ΚΑΝΟΝΑΣ X < 15% (Propose 1-2)
if pX < 0.15:
    base = "1-2"

# 7. HIGH RISK & TRAP ALERTS
if total > 0 and (p1 + p2) < 0.40:
    warning = "⚠️ HIGH RISK MATCH: Statistics are very low, abstention is recommended."
elif odd1 <= 1.55 and pX > 0.28:
    warning = "⚠️ ΠΑΓΙΔΑ ΣΤΟ Χ: Το φαβορί δυσκολεύεται στα στατιστικά. Το φαβορί θα δυσκολευτεί."

proposal = f"{base} (VALUE)"
st.session_state.current_proposal = proposal
color = "#2ecc71" if conf >= 65 else "#f1c40f" if conf >= 45 else "#e74c3c"

# ==============================
# UI OUTPUT
# ==============================
st.markdown(f"""
<div class="result-card">
    <div style="color:gray;font-weight:bold;margin-bottom:5px;">📊 BetAnalyzer v17.2.9 (Final Base)</div>
    <div style="font-size:3.5rem;font-weight:900;color:#1e3c72;line-height:1;">{proposal}</div>
    <div style="font-size:1.8rem;font-weight:bold;color:{color};margin-top:10px;">{conf}% Confidence</div>
</div>
""", unsafe_allow_html=True)

if warning:
    st.markdown(f'<div class="warning-box">{warning}</div>', unsafe_allow_html=True)

# ==============================
# INPUT FIELDS
# ==============================
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

# ==============================
# CHART & LIVE PROBS
# ==============================
fig = go.Figure()
fig.add_trace(go.Bar(name='Bookie %', x=['1', 'X', '2'], y=[pm1*100, pmX*100, pm2*100], marker_color='#1e3c72'))
fig.add_trace(go.Bar(name='Real_Stats %', x=['1', 'X', '2'], y=[p1*100, pX*100, p2*100], marker_color='#2ecc71'))
fig.update_layout(barmode='group', height=300, margin=dict(l=20, r=20, t=20, b=20))
st.plotly_chart(fig, use_container_width=True)

st.markdown(f"**[LIVE PROBS]: 1: {p1*100:.1f}% | X: {pX*100:.1f}% | 2: {p2*100:.1f}%**")
st.caption("v17.2.9: Fixed Invincibility & Double Chance Logic")
