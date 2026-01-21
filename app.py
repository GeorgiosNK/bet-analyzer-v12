import streamlit as st
import plotly.graph_objects as go
import streamlit.components.v1 as components

# ==============================
# CONFIG
# ==============================
st.set_page_config(page_title="Bet Analyzer v13.0.1 PRO", page_icon="⚽", layout="centered")

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
    background: #ffffff; padding: 1.5rem; border-radius: 15px;
    border: 2px solid #1e3c72; text-align: center;
    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
}
.warning-box {
    background-color: #fff3cd; color: #856404; padding: 12px; 
    border-radius: 8px; border: 1px solid #ffeeba; margin: 10px 0;
    font-weight: bold; text-align: center;
}
</style>
""", unsafe_allow_html=True)

# ==============================
# STATE
# ==============================
if 'hw' not in st.session_state:
    st.session_state.update({'hw':0,'hd':0,'hl':0,'aw':0,'ad':0,'al':0})
if 'o1' not in st.session_state:
    st.session_state.update({'o1':"1.00",'ox':"1.00",'o2':"1.00"})

def reset_all():
    for k in ['hw','hd','hl','aw','ad','al']: st.session_state[k] = 0
    st.session_state.o1 = st.session_state.ox = st.session_state.o2 = "1.00"

# ==============================
# SIDEBAR
# ==============================
with st.sidebar:
    st.header("🏆 Control Panel")
    st.button("🧹 Reset All", on_click=reset_all, use_container_width=True)
    o1_input = st.text_input("Άσος (1)", key="o1")
    ox_input = st.text_input("Ισοπαλία (X)", key="ox")
    o2_input = st.text_input("Διπλό (2)", key="o2")

def sf(x):
    try: 
        v = float(str(x).replace(',','.'))
        return v if v > 0 else 1.0
    except: return 1.0

odd1, oddX, odd2 = sf(o1_input), sf(ox_input), sf(o2_input)

# ==============================
# CALCULATIONS
# ==============================
h_total = st.session_state.hw + st.session_state.hd + st.session_state.hl
a_total = st.session_state.aw + st.session_state.ad + st.session_state.al
total_games = h_total + a_total

inv = (1/odd1 + 1/oddX + 1/odd2)
p_m1, p_mX, p_m2 = (1/odd1)/inv, (1/oddX)/inv, (1/odd2)/inv

alpha = min(1.0, total_games / 20)
h_wr = st.session_state.hw / h_total if h_total > 0 else p_m1
a_wr = st.session_state.aw / a_total if a_total > 0 else p_m2
p_1 = alpha * h_wr + (1-alpha) * p_m1
p_2 = alpha * a_wr + (1-alpha) * p_m2
p_X = max(0.05, 1 - p_1 - p_2)
s = p_1 + p_X + p_2
p_1, p_X, p_2 = p_1/s, p_X/s, p_2/s

# Value
v1, vX, v2 = p_1 - p_m1, p_X - p_mX, p_2 - p_m2
vals = {'1': v1, 'X': vX, '2': v2}
best_pick = max(vals, key=vals.get)
best_val = vals[best_pick]

# ==============================
# ALWAYS PROVIDE PROPOSAL
# ==============================
mode = "⚖️ BLIND MODE" if total_games == 0 else "📊 CALIBRATED MODEL"
suffix = ""
if best_val < 0.05:
    suffix = " (LOW CONF)"
else:
    suffix = " (VALUE)"

proposal = f"{best_pick}{suffix}"

warning = ""
if best_val < 0.05:
    warning = "⚠️ ΠΡΟΣΟΧΗ: Το μοντέλο δεν εντοπίζει ισχυρό πλεονέκτημα."
if odd1 <= 1.50 and p_X > 0.25:
    warning = "⚠️ ΠΑΓΙΔΑ ΦΑΒΟΡΙ – ΥΨΗΛΟ Χ"
if total_games > 0 and (p_1 + p_2) < 0.40:
    warning = "⚠️ HIGH RISK: Πολύ χαμηλά στατιστικά νίκης."

conf = int(min(100, (alpha * 50) + (max(0, best_val) * 250)))
conf = max(5, conf)
color = "#2ecc71" if conf >= 75 else "#f1c40f" if conf >= 50 else "#e74c3c"

# ==============================
# UI
# ==============================
st.markdown(f"""
<div class="result-card">
    <div style="color:gray;font-weight:bold;">{mode}</div>
    <div style="font-size:3.5rem;font-weight:900;color:#1e3c72;">{proposal}</div>
    <div style="font-size:1.8rem;font-weight:bold;color:{color};">{conf}% Confidence</div>
</div>
""", unsafe_allow_html=True)

if warning: st.markdown(f'<div class="warning-box">{warning}</div>', unsafe_allow_html=True)

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

fig = go.Figure()
fig.add_trace(go.Bar(name='Bookmaker %', x=['1','X','2'], y=[p_m1*100, p_mX*100, p_m2*100], marker_color='#1e3c72'))
fig.add_trace(go.Bar(name='Model %', x=['1','X','2'], y=[p_1*100, p_X*100, p_2*100], marker_color='#2ecc71'))
fig.update_layout(barmode='group', height=300, margin=dict(l=20, r=20, t=20, b=20))
st.plotly_chart(fig, use_container_width=True)
