import streamlit as st
import plotly.graph_objects as go
import streamlit.components.v1 as components

# ==============================
# CONFIG & CSS (v17.0.7)
# ==============================
st.set_page_config(page_title="Bet Analyzer v17.0.7", page_icon="⚽", layout="centered")

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
# STATE & INPUTS
# ==============================
if 'hw' not in st.session_state: st.session_state.update({'hw':0,'hd':0,'hl':0,'aw':0,'ad':0,'al':0})
if 'o1' not in st.session_state: st.session_state.update({'o1':"1.00",'ox':"1.00",'o2':"1.00"})

with st.sidebar:
    st.header("🏆 Control Panel")
    if st.button("🧹 Clear Stats & Odds", use_container_width=True):
        for k in ['hw','hd','hl','aw','ad','al']: st.session_state[k] = 0
        st.session_state.o1 = st.session_state.ox = st.session_state.o2 = "1.00"
    o1_i = st.text_input("Άσος (1)", key="o1")
    ox_i = st.text_input("Ισοπαλία (X)", key="ox")
    o2_i = st.text_input("Διπλό (2)", key="o2")

def sf(x):
    try: return float(str(x).replace(',','.')) if float(str(x).replace(',','.')) > 0 else 1.0
    except: return 1.0

odd1, oddX, odd2 = sf(o1_i), sf(ox_i), sf(o2_i)

# ==============================
# ENGINE (v17.0.7)
# ==============================
h_t = st.session_state.hw + st.session_state.hd + st.session_state.hl
a_t = st.session_state.aw + st.session_state.ad + st.session_state.al
total = h_t + a_t

inv = (1/odd1 + 1/oddX + 1/odd2)
pm1, pmX, pm2 = (1/odd1)/inv, (1/oddX)/inv, (1/odd2)/inv

alpha = min(1.0, total / 15)
h_wr = st.session_state.hw / h_t if h_t > 0 else pm1
a_wr = st.session_state.aw / a_t if a_t > 0 else pm2
p1 = alpha * h_wr + (1-alpha) * pm1
p2 = alpha * a_wr + (1-alpha) * pm2
pX = max(0.01, 1 - p1 - p2)
s = p1 + pX + p2
p1, pX, p2 = p1/s, pX/s, p2/s

v1, vX, v2 = p1 - pm1, pX - pmX, p2 - pm2
vals = {'1': v1, 'X': vX, '2': v2}
best_v_key = max(vals, key=vals.get)
edge = vals[best_v_key]
conf = int(min(100, (alpha * 55) + (max(0, edge) * 220)))

# --- LOGIC HIERARCHY v17.0.7 ---
if pX < 0.15:
    res = "1" if p1 > p2 else "2"
    # ΝΕΟΣ ΚΑΝΟΝΑΣ: Κάλυψη αν η απόδοση είναι > 2.80
    if res == "1" and odd1 > 2.80: base = "1 (1X)"
    elif res == "2" and odd2 > 2.80: base = "2 (X2)"
    else: base = res
elif pX >= 0.40:
    base = "X (1X)" if st.session_state.hw + st.session_state.hd > st.session_state.aw + st.session_state.ad else "X (X2)"
elif abs(p1 - p2) < 0.12:
    base = "X (1X)" if st.session_state.hw + st.session_state.hd > st.session_state.aw + st.session_state.ad else "X (X2)"
else:
    # Default με έλεγχο απόδοσης για κάλυψη
    if best_v_key == "1" and odd1 > 2.80: base = "1 (1X)"
    elif best_v_key == "2" and odd2 > 2.80: base = "2 (X2)"
    else: base = best_v_key

proposal = f"{base} {'(VALUE)' if edge >= 0.05 else '(LOW CONF)'}"
color = "#2ecc71" if conf >= 75 else "#f1c40f" if conf >= 50 else "#e74c3c"

warning = ""
if total > 0 and (p1 + p2) < 0.40: warning = "⚠️ HIGH RISK MATCH: Statistics are very low, abstention is recommended."
elif odd1 <= 1.55 and pX > 0.28: warning = "⚠️ ΠΑΓΙΔΑ ΣΤΟ Χ: Το φαβορί δυσκολεύεται στα στατιστικά."

# ==============================
# UI OUTPUT
# ==============================
st.markdown(f"""
<div class="result-card">
    <div style="color:gray;font-weight:bold;margin-bottom:5px;">📊 CALIBRATED MODEL v17.0.7</div>
    <div style="font-size:3.5rem;font-weight:900;color:#1e3c72;line-height:1;">{proposal}</div>
    <div style="font-size:1.8rem;font-weight:bold;color:{color};margin-top:10px;">{conf}% Confidence</div>
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
fig.add_trace(go.Bar(name='Bookie %', x=['1', 'X', '2'], y=[pm1*100, pmX*100, pm2*100], marker_color='#1e3c72'))
fig.add_trace(go.Bar(name='Real_Stats %', x=['1', 'X', '2'], y=[p1*100, pX*100, p2*100], marker_color='#2ecc71'))
fig.update_layout(barmode='group', height=350, margin=dict(l=20, r=20, t=20, b=20))
st.plotly_chart(fig, use_container_width=True)
