import streamlit as st
import plotly.graph_objects as go
import streamlit.components.v1 as components

# ==============================
# CONFIG
# ==============================
st.set_page_config(page_title="Bet Analyzer v13.0 VALUE PRO", page_icon="⚽", layout="centered")

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
# CSS
# ==============================
st.markdown("""
<style>
.result-card {
    background: #ffffff;
    padding: 1.5rem;
    border-radius: 15px;
    border: 2px solid #1e3c72;
    text-align: center;
    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
}
.warning-box {
    background-color: #fff3cd;
    color: #856404;
    padding: 12px;
    border-radius: 8px;
    border: 1px solid #ffeeba;
    margin: 10px 0;
    font-weight: bold;
    text-align: center;
}
</style>
""", unsafe_allow_html=True)

# ==============================
# STATE INIT
# ==============================
if 'hw' not in st.session_state:
    st.session_state.update({'hw':0,'hd':0,'hl':0,'aw':0,'ad':0,'al':0})
if 'o1' not in st.session_state:
    st.session_state.update({'o1':"1.00",'ox':"1.00",'o2':"1.00"})

def reset_all():
    for k in ['hw','hd','hl','aw','ad','al']:
        st.session_state[k] = 0
    st.session_state.o1 = st.session_state.ox = st.session_state.o2 = "1.00"

# ==============================
# SIDEBAR
# ==============================
with st.sidebar:
    st.header("🏆 Control Panel")
    st.button("🧹 Reset", on_click=reset_all)
    o1 = st.text_input("Άσος (1)", key="o1")
    ox = st.text_input("Ισοπαλία (X)", key="ox")
    o2 = st.text_input("Διπλό (2)", key="o2")

def sf(x):
    try: return float(str(x).replace(',','.'))
    except: return 1.0

odd1, oddX, odd2 = sf(o1), sf(ox), sf(o2)

# ==============================
# BASIC COUNTS
# ==============================
h_total = st.session_state.hw + st.session_state.hd + st.session_state.hl
a_total = st.session_state.aw + st.session_state.ad + st.session_state.al
total_games = h_total + a_total

# ==============================
# MARKET PROBABILITIES (NO MARGIN)
# ==============================
inv = (1/odd1 + 1/oddX + 1/odd2)
p_m1 = (1/odd1)/inv
p_mX = (1/oddX)/inv
p_m2 = (1/odd2)/inv

# ==============================
# MODEL PROBABILITIES (BLENDED)
# ==============================
alpha = min(1.0, total_games / 20)   # confidence in stats

h_win_rate = st.session_state.hw / h_total if h_total > 0 else p_m1
a_win_rate = st.session_state.aw / a_total if a_total > 0 else p_m2
draw_rate  = (st.session_state.hd + st.session_state.ad) / total_games if total_games > 0 else p_mX

p_1 = alpha * h_win_rate + (1-alpha) * p_m1
p_2 = alpha * a_win_rate + (1-alpha) * p_m2
p_X = max(0.01, 1 - p_1 - p_2)

# normalize safety
s = p_1 + p_X + p_2
p_1, p_X, p_2 = p_1/s, p_X/s, p_2/s

mode = "⚖️ BLIND MODE" if total_games == 0 else "📊 CALIBRATED MODEL"

# ==============================
# VALUE (EDGE)
# ==============================
v1 = p_1 - p_m1
vX = p_X - p_mX
v2 = p_2 - p_m2

values = {'1':v1, 'X':vX, '2':v2}
best_pick = max(values, key=values.get)
best_value = values[best_pick]

# ==============================
# FINAL PROPOSAL
# ==============================
proposal = "❌ NO BET"
warning = ""

if best_value >= 0.05:
    if best_pick == '1':
        proposal = "1 (VALUE)"
    elif best_pick == 'X':
        proposal = "X (VALUE)"
    else:
        proposal = "2 (VALUE)"
else:
    warning = "⚠️ ΧΩΡΙΣ VALUE – ΑΠΟΧΗ"

# trap warning
if odd1 <= 1.50 and p_X > 0.25:
    warning = "⚠️ ΠΑΓΙΔΑ ΦΑΒΟΡΙ – ΥΨΗΛΟ Χ"

# ==============================
# CONFIDENCE
# ==============================
conf = int(min(100, (total_games/30)*40 + best_value*100))
conf = max(5, conf)

color = "#2ecc71" if conf >= 75 else "#f1c40f" if conf >= 50 else "#e74c3c"

# ==============================
# UI RESULT
# ==============================
st.markdown(f"""
<div class="result-card">
    <div style="color:gray;font-weight:bold">{mode}</div>
    <div style="font-size:3rem;font-weight:900;color:#1e3c72">{proposal}</div>
    <div style="font-size:1.5rem;font-weight:bold;color:{color}">
        {conf}% Confidence
    </div>
</div>
""", unsafe_allow_html=True)

if warning:
    st.markdown(f'<div class="warning-box">{warning}</div>', unsafe_allow_html=True)

# ==============================
# INPUTS
# ==============================
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
# CHART
# ==============================
fig = go.Figure()
fig.add_bar(name='Bookmaker %', x=['1','X','2'], y=[p_m1*100, p_mX*100, p_m2*100])
fig.add_bar(name='Model %', x=['1','X','2'], y=[p_1*100, p_X*100, p_2*100])
fig.update_layout(barmode='group', height=300)
st.plotly_chart(fig, use_container_width=True)
