import streamlit as st
import plotly.graph_objects as go
import streamlit.components.v1 as components

# ==============================
# CONFIG - ΔΙΟΡΘΩΘΗΚΕ ΤΟ PAGE_ICON
# ==============================
st.set_page_config(page_title="BetAnalyzer v17.2.6", page_icon="⚽", layout="centered")

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

if 'hw' not in st.session_state:
    st.session_state.update({'hw':0,'hd':0,'hl':0,'aw':0,'ad':0,'al':0})
if 'o1' not in st.session_state:
    st.session_state.update({'o1':"1.00",'ox':"1.00",'o2':"1.00"})

def reset_all():
    for k in ['hw','hd','hl','aw','ad','al']: st.session_state[k] = 0
    st.session_state.o1 = st.session_state.ox = st.session_state.o2 = "1.00"

with st.sidebar:
    st.header("🏆 Control Panel")
    st.button("🧹 Clear Stats & Odds", on_click=reset_all, use_container_width=True)
    o1_i = st.text_input("Άσος (1)", key="o1")
    ox_i = st.text_input("Ισοπαλία (X)", key="ox")
    o2_i = st.text_input("Διπλό (2)", key="o2")

def sf(x):
    try: 
        v = float(str(x).replace(',','.'))
        return v if v > 0 else 1.0
    except: return 1.0

odd1, oddX, odd2 = sf(o1_i), sf(ox_i), sf(o2_i)

h_t = st.session_state.hw + st.session_state.hd + st.session_state.hl
a_t = st.session_state.aw + st.session_state.ad + st.session_state.al
total = h_t + a_t

inv = (1/odd1 + 1/oddX + 1/odd2)
pm1, pmX, pm2 = (1/odd1)/inv, (1/oddX)/inv, (1/odd2)/inv
alpha = min(1.0, total / 15)

h_wr = (st.session_state.hw - (st.session_state.hl * 0.3)) / h_t if h_t > 0 else pm1
a_wr = (st.session_state.aw - (st.session_state.al * 0.3)) / a_t if a_t > 0 else pm2

p1 = alpha * h_wr + (1-alpha) * pm1
p2 = alpha * a_wr + (1-alpha) * pm2
p1, p2 = max(0.10, p1), max(0.10, p2)
pX = max(0.01, 1 - p1 - p2)

real_h_draw = st.session_state.hd / h_t if h_t > 0 else 0.25
real_a_draw = st.session_state.ad / a_t if a_t > 0 else 0.25
avg_draw = (real_h_draw + real_a_draw) / 2

if pX > 0.50 and avg_draw < 0.40:
    diff = pX - 0.50
    p1 += diff * 0.5
    p2 += diff * 0.5
    pX = 0.50

s = p1 + pX + p2
p1, pX, p2 = p1/s, pX/s, p2/s

# ==============================
# LOGIC ENGINE v17.2.6
# ==============================
real_probs = {'1': p1, 'X': pX, '2': p2}
res = max(real_probs, key=real_probs.get)
odd_check = odd1 if res == "1" else oddX if res == "X" else odd2
conf = int(real_probs[res] * 100)

base = res
has_cover_reason = pX >= 0.20  # ΤΟ ΟΡΙΟ ΠΟΥ ΣΥΜΦΩΝΗΣΑΜΕ

if res == "1" and odd_check >= 2.00 and has_cover_reason:
    base = "1X"
elif res == "2" and odd_check >= 2.00 and has_cover_reason:
    base = "X2"
elif 0.20 <= pX < 0.40 and res != "X":
    base = f"{res} ({'1X' if res == '1' else 'X2'})"
elif pX >= 0.40:
    base = "X"

h_pos = (st.session_state.hw + st.session_state.hd) / h_t if h_t > 0 else 0
a_pos = (st.session_state.aw + st.session_state.ad) / a_t if a_t > 0 else 0

if a_pos >= 2 * h_pos and h_pos > 0 and has_cover_reason: base = "X2"
elif h_pos >= 2 * a_pos and a_pos > 0 and has_cover_reason: base = "1X"

# Override για ξερό σημείο αν το Χ είναι χαμηλό
if res == "1" and (p1 > 0.70 or pX < 0.20): base = "1"
elif res == "2" and (p2 > 0.70 or pX < 0.20): base = "2"

proposal = f"{base} (VALUE)"
color = "#2ecc71" if conf >= 65 else "#f1c40f" if conf >= 45 else "#e74c3c"

st.markdown(f"""
<div class="result-card">
    <div style="color:gray;font-weight:bold;margin-bottom:5px;">📊 BetAnalyzer v17.2.6</div>
    <div style="font-size:3.5rem;font-weight:900;color:#1e3c72;line-height:1;">{proposal}</div>
    <div style="font-size:1.8rem;font-weight:bold;color:{color};margin-top:10px;">{conf}% Confidence</div>
</div>
""", unsafe_allow_html=True)

# ... (υπόλοιπο UI code ίδιο)
