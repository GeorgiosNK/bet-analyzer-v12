import streamlit as st
import plotly.graph_objects as go
import streamlit.components.v1 as components

# ==============================
# CONFIG
# ==============================
st.set_page_config(page_title="Bet Analyzer v13.0.9 STRICT ORDER", page_icon="⚽", layout="centered")

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
    o1_i = st.text_input("Άσος (1)", key="o1")
    ox_i = st.text_input("Ισοπαλία (X)", key="ox")
    o2_i = st.text_input("Διπλό (2)", key="o2")

def sf(x):
    try: 
        v = float(str(x).replace(',','.'))
        return v if v > 0 else 1.0
    except: return 1.0

odd1, oddX, odd2 = sf(o1_i), sf(ox_i), sf(o2_i)

# ==============================
# CALCULATIONS
# ==============================
h_t = st.session_state.hw + st.session_state.hd + st.session_state.hl
a_t = st.session_state.aw + st.session_state.ad + st.session_state.al
total = h_t + a_t

inv = (1/odd1 + 1/oddX + 1/odd2)
pm1, pmX, pm2 = (1/odd1)/inv, (1/oddX)/inv, (1/odd2)/inv

alpha = min(1.0, total / 20)
h_wr = st.session_state.hw / h_t if h_t > 0 else pm1
a_wr = st.session_state.aw / a_t if a_t > 0 else pm2
p1 = alpha * h_wr + (1-alpha) * pm1
p2 = alpha * a_wr + (1-alpha) * pm2
pX = max(0.05, 1 - p1 - p2)
s = p1 + pX + p2
p1, pX, p2 = p1/s, pX/s, p2/s

v1, vX, v2 = p1 - pm1, pX - pmX, p2 - pm2
vals = {'1': v1, 'X': vX, '2': v2}

# ==============================
# FINAL LOGIC ENGINE v13.0.9 (STRICT ORDER)
# ==============================
h_pos = st.session_state.hw + st.session_state.hd
a_pos = st.session_state.aw + st.session_state.ad

best_v_key = max(vals, key=vals.get)
current_edge = vals[best_v_key]
conf = int(min(100, (alpha * 55) + (max(0, current_edge) * 220)))

# --- ΙΕΡΑΡΧΙΑ ΑΠΟΦΑΣΕΩΝ ---

# 1. UPSET DETECTOR (Αν το confidence είναι χαμηλό και ο φιλοξενούμενος έχει νίκες)
if conf < 30 and st.session_state.aw > st.session_state.hw:
    base = "X2 (UPSET ALERT)"
    edge = v2
# 2. ΚΑΘΑΡΟ ΦΑΒΟΡΙ (Πάνω από 55% για να αποφεύγουμε τα οριακά)
elif p1 >= 0.55:
    base = "1"
    edge = v1
elif p2 >= 0.55:
    base = "2"
    edge = v2
# 3. ΚΑΝΟΝΑΣ ΙΣΟΠΑΛΙΑΣ (X)
elif pX >= 0.40:
    edge = vX
    if st.session_state.aw > st.session_state.hw or a_pos > h_pos:
        base = "X (X2)"
    elif st.session_state.hw > st.session_state.aw or h_pos > a_pos:
        base = "X (1X)"
    else:
        base = "X"
# 4. DEFAULT: ΤΟ ΣΗΜΕΙΟ ΜΕ ΤΟ ΜΕΓΑΛΥΤΕΡΟ VALUE
else:
    edge = current_edge
    if abs(p1 - p2) < 0.12:
        base = "1X" if (h_pos >= a_pos) else "X2"
    else:
        base = best_v_key

proposal = f"{base} {'(VALUE)' if edge >= 0.05 else '(LOW CONF)'}"

# UI Colors & Warnings
color = "#2ecc71" if conf >= 75 else "#f1c40f" if conf >= 50 else "#e74c3c"
warning = ""
if odd1 <= 1.55 and pX > 0.28: warning = "⚠️ ΠΑΓΙΔΑ ΦΑΒΟΡΙ: Στατιστικά αυξημένη πιθανότητα Χ."
if total > 0 and (p1 + p2) < 0.35: warning = "⚠️ HIGH RISK MATCH: Πολύ χαμηλά ποσοστά νίκης."

# ==============================
# UI OUTPUT
# ==============================
st.markdown(f"""
<div class="result-card">
    <div style="color:gray;font-weight:bold;margin-bottom:5px;">{"📊 CALIBRATED MODEL" if total > 0 else "⚖️ BLIND MODE"}</div>
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

# Plotly Chart
fig = go.Figure()
fig.add_trace(go.Bar(name='Bookie %', x=['1', 'X', '2'], y=[pm1*100, pmX*100, pm2*100], marker_color='#1e3c72',
                     text=[f"<b>{pm1*100:.1f}%</b>", f"<b>{pmX*100:.1f}%</b>", f"<b>{pm2*100:.1f}%</b>"],
                     textposition='inside', textfont=dict(color="white", size=14)))
fig.add_trace(go.Bar(name='Model %', x=['1', 'X', '2'], y=[p1*100, pX*100, p2*100], marker_color='#2ecc71',
                     text=[f"<b>{p1*100:.1f}%</b>", f"<b>{pX*100:.1f}%</b>", f"<b>{p2*100:.1f}%</b>"],
                     textposition='inside', textfont=dict(color="white", size=14)))
fig.update_layout(barmode='group', height=350, xaxis=dict(type='category'), margin=dict(l=20, r=20, t=20, b=20))
st.plotly_chart(fig, use_container_width=True)
