import streamlit as st
import plotly.graph_objects as go

# ==============================
# CONFIG & CSS (Αυστηρά v17.0.6 Style)
# ==============================
st.set_page_config(page_title="Bet Analyzer v17.0.7", page_icon="⚽", layout="centered")

st.markdown("""
<style>
/* Auto-select κειμένου για γρήγορη εισαγωγή */
input {
    select-all: true;
}
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
# SIDEBAR (Control Panel v17.0.6)
# ==============================
with st.sidebar:
    st.header("🏆 Control Panel")
    if st.button("清理 Stats & Odds", use_container_width=True):
        st.rerun()
    
    # Text inputs για αποδόσεις με υποστήριξη υποδιαστολής
    o1_raw = st.text_input("Άσος (1)", value="1.00")
    ox_raw = st.text_input("Ισοπαλία (X)", value="1.00")
    o2_raw = st.text_input("Διπλό (2)", value="1.00")

def parse_odd(val):
    try: return float(val.replace(',', '.'))
    except: return 1.0

odd1, oddX, odd2 = parse_odd(o1_raw), parse_odd(ox_raw), parse_odd(o2_raw)

# ==============================
# ΣΤΑΤΙΣΤΙΚΑ (Layout v17.0.6)
# ==============================
st.subheader("Στατιστικά (0 αν δεν υπάρχουν δεδομένα)")
c1, c2 = st.columns(2)
with c1:
    st.markdown("🏠 **ΓΗΠΕΔΟΥΧΟΣ**")
    hw = st.number_input("Νίκες", 0, 100, key="hw")
    hd = st.number_input("Ισοπαλίες", 0, 100, key="hd")
    hl = st.number_input("Ήττες", 0, 100, key="hl")
with c2:
    st.markdown("🚀 **ΦΙΛΟΞΕΝΟΥΜΕΝΟΣ**")
    aw = st.number_input("Νίκες", 0, 100, key="aw")
    ad = st.number_input("Ισοπαλίες", 0, 100, key="ad")
    al = st.number_input("Ήττες", 0, 100, key="al")

# ==============================
# ENGINE (v17.0.7 Core Logic)
# ==============================
h_t, a_t = (hw+hd+hl), (aw+ad+al)
total = h_t + a_t

# Bookie Probs
inv = (1/odd1 + 1/oddX + 1/odd2)
pm1, pmX, pm2 = (1/odd1)/inv, (1/oddX)/inv, (1/odd2)/inv

# Real Stats
alpha = min(1.0, total / 15)
h_wr = hw / h_t if h_t > 0 else pm1
a_wr = aw / a_t if a_t > 0 else pm2
p1 = alpha * h_wr + (1-alpha) * pm1
p2 = alpha * a_wr + (1-alpha) * pm2
pX = max(0.01, 1 - p1 - p2)
p_sum = p1 + pX + p2
p1, pX, p2 = p1/p_sum, pX/p_sum, p2/p_sum

# Value & Confidence
v1, vX, v2 = p1 - pm1, pX - pmX, p2 - pm2
vals = {'1': v1, 'X': vX, '2': v2}
best_v_key = max(vals, key=vals.get)
edge = vals[best_v_key]
conf = int(min(100, (alpha * 55) + (max(0, edge) * 220)))

# --- HIERARCHY LOGIC (Including new 2.80 Rule) ---
if pX < 0.15:
    res = "1" if p1 > p2 else "2"
    o_check = odd1 if res == "1" else odd2
    if o_check > 2.80: base = f"{res} ({res}{'X' if res=='1' else '2'})"
    else: base = res
elif pX >= 0.40:
    base = "X"
elif abs(p1 - p2) < 0.12:
    base = "X"
else:
    res = best_v_key
    o_check = odd1 if res == "1" else odd2
    if o_check > 2.80: base = f"{res} ({res}{'X' if res=='1' else '2'})"
    else: base = res

# Προσθήκη Κάλυψης (Dominant Point)
if pX >= 0.15 and pX < 0.40 and abs(p1-p2) >= 0.12:
    if (hw + hd) > (aw + ad): base = f"{base} (1X)"
    else: base = f"{base} (X2)"

proposal = f"{base} (VALUE)"
color = "#2ecc71" if conf >= 75 else "#f1c40f" if conf >= 50 else "#e74c3c"

# Warning Logic
warning = ""
if total > 0 and (p1 + p2) < 0.40:
    warning = "⚠️ HIGH RISK MATCH: Statistics are very low, abstention is recommended."
elif odd1 <= 1.55 and pX > 0.28:
    warning = "⚠️ ΠΑΓΙΔΑ ΣΤΟ Χ: Το φαβορί δυσκολεύεται στα στατιστικά."

# ==============================
# UI OUTPUT (v17.0.6 Layout)
# ==============================
st.markdown(f"""
<div class="result-card">
    <div style="color:gray;font-weight:bold;margin-bottom:5px;">REAL STATS ANALYSIS v17.0.7</div>
    <div style="font-size:3.5rem;font-weight:900;color:#1e3c72;line-height:1;">{proposal}</div>
    <div style="font-size:1.8rem;font-weight:bold;color:{color};margin-top:10px;">{conf}% Confidence</div>
</div>
""", unsafe_allow_html=True)

if warning:
    st.markdown(f'<div class="warning-box">{warning}</div>', unsafe_allow_html=True)

# Γράφημα
fig = go.Figure()
fig.add_trace(go.Bar(name='Bookie %', x=['1', 'X', '2'], y=[pm1*100, pmX*100, pm2*100], marker_color='#1e3c72'))
fig.add_trace(go.Bar(name='Real_Stats %', x=['1', 'X', '2'], y=[p1*100, pX*100, p2*100], marker_color='#2ecc71'))
fig.update_layout(barmode='group', height=350, margin=dict(l=20, r=20, t=20, b=20))
st.plotly_chart(fig, use_container_width=True)
