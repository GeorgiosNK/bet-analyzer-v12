import streamlit as st
import plotly.graph_objects as go
import streamlit.components.v1 as components

# ==============================
# CONFIG & CSS (ΑΘΙΚΤΑ)
# ==============================
st.set_page_config(page_title="Bet Analyzer v17.2.2", page_icon="⚽", layout="centered")

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
# STATE & CALCULATIONS
# ==============================
if 'hw' not in st.session_state: st.session_state.update({'hw':0,'hd':0,'hl':0,'aw':0,'ad':0,'al':0})
if 'o1' not in st.session_state: st.session_state.update({'o1':"1.00",'ox':"1.00",'o2':"1.00"})

def sf(x):
    try: 
        v = float(str(x).replace(',','.'))
        return v if v > 0 else 1.0
    except: return 1.0

odd1, oddX, odd2 = sf(st.session_state.o1), sf(st.session_state.ox), sf(st.session_state.o2)

h_t = st.session_state.hw + st.session_state.hd + st.session_state.hl
a_t = st.session_state.aw + st.session_state.ad + st.session_state.al
total = h_t + a_t

# Υπολογισμός Positive Percentages για το UI
h_pos_pct = ((st.session_state.hw + st.session_state.hd) / h_t * 100) if h_t > 0 else 0
a_pos_pct = ((st.session_state.aw + st.session_state.ad) / a_t * 100) if a_t > 0 else 0

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

# ==============================
# LOGIC ENGINE v17.2.2 (ΒΕΛΤΙΩΜΕΝΟ)
# ==============================
real_probs = {'1': p1, 'X': pX, '2': p2}
res = max(real_probs, key=real_probs.get) 
odd_check = odd1 if res == "1" else oddX if res == "X" else odd2
conf = int(real_probs[res] * 100)

# ΝΕΑ ΛΟΓΙΚΗ: Συνδυασμός X με το πιθανότερο σημείο αν pX > 40%
if pX >= 0.40:
    if p2 > p1 and p2 > 0.30: base = "X (X2)"
    elif p1 > p2 and p1 > 0.30: base = "X (1X)"
    else: base = "X"
elif odd_check >= 2.80:
    if res == "1" and (pX > 0.15 or st.session_state.ad > 0): base = "1 (1X)"
    elif res == "2" and (pX > 0.15 or st.session_state.hd > 0): base = "2 (X2)"
    else: base = res
else:
    base = res

# Κανόνας Double Positive Percentage
if a_pos_pct >= 2 * h_pos_pct and h_pos_pct > 0: base = "X2"
elif h_pos_pct >= 2 * a_pos_pct and a_pos_pct > 0: base = "1X"

proposal = f"{base} (VALUE)"
color = "#2ecc71" if conf >= 65 else "#f1c40f" if conf >= 45 else "#e74c3c"

# ==============================
# UI OUTPUT
# ==============================
st.markdown(f"""
<div class="result-card">
    <div style="color:gray;font-weight:bold;margin-bottom:5px;">📊 CALIBRATED MODEL v17.2.2</div>
    <div style="font-size:3.5rem;font-weight:900;color:#1e3c72;line-height:1;">{proposal}</div>
    <div style="font-size:1.8rem;font-weight:bold;color:{color};margin-top:10px;">{conf}% Confidence</div>
</div>
""", unsafe_allow_html=True)

st.markdown("---")
c1, c2 = st.columns(2)
with c1:
    st.subheader(f"🏠 Γηπεδούχος ({h_pos_pct:.1f}%)") # Εμφάνιση Ποσοστού
    st.number_input("Νίκες", 0, 100, key="hw")
    st.number_input("Ισοπαλίες", 0, 100, key="hd")
    st.number_input("Ήττες", 0, 100, key="hl")
with c2:
    st.subheader(f"🚀 Φιλοξενούμενος ({a_pos_pct:.1f}%)") # Εμφάνιση Ποσοστού
    st.number_input("Νίκες", 0, 100, key="aw")
    st.number_input("Ισοπαλίες", 0, 100, key="ad")
    st.number_input("Ήττες", 0, 100, key="al")

# Plotly Chart (ΑΘΙΚΤΟ)
fig = go.Figure()
fig.add_trace(go.Bar(name='Bookie %', x=['1', 'X', '2'], y=[pm1*100, pmX*100, pm2*100], marker_color='#1e3c72'))
fig.add_trace(go.Bar(name='Real_Stats %', x=['1', 'X', '2'], y=[p1*100, pX*100, p2*100], marker_color='#2ecc71'))
st.plotly_chart(fig, use_container_width=True)
