import streamlit as st
import plotly.graph_objects as go

# ==============================
# CONFIG & CSS
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
/* Διόρθωση για αυτόματη επιλογή κειμένου στα inputs */
input {
    select-all: true;
}
</style>
""", unsafe_allow_html=True)

# ==============================
# STATE & INPUTS (Επαναφορά λειτουργικότητας)
# ==============================
with st.sidebar:
    st.header("🏆 Control Panel")
    # Χρήση st.number_input με step=0 για καλύτερο έλεγχο
    o1 = st.number_input("Άσος (1)", value=1.00, step=0.01, format="%.2f")
    ox = st.number_input("Ισοπαλία (X)", value=1.00, step=0.01, format="%.2f")
    o2 = st.number_input("Διπλό (2)", value=1.00, step=0.01, format="%.2f")

# --- Στατιστικά Εισαγωγής ---
st.subheader("Στατιστικά Ομάδων")
c1, c2 = st.columns(2)
with c1:
    st.markdown("🏠 **ΓΗΠΕΔΟΥΧΟΣ**")
    hw = st.number_input("Νίκες", 0, 100, key="hw_in")
    hd = st.number_input("Ισοπαλίες", 0, 100, key="hd_in")
    hl = st.number_input("Ήττες", 0, 100, key="hl_in")
with c2:
    st.markdown("🚀 **ΦΙΛΟΞΕΝΟΥΜΕΝΟΣ**")
    aw = st.number_input("Νίκες", 0, 100, key="aw_in")
    ad = st.number_input("Ισοπαλίες", 0, 100, key="ad_in")
    al = st.number_input("Ήττες", 0, 100, key="al_in")

# ==============================
# ENGINE (v17.0.7 Logic)
# ==============================
h_t = hw + hd + hl
a_t = aw + ad + al
total = h_t + a_t

# Υπολογισμός Γκανιότας & Πιθανοτήτων Bookie
inv = (1/o1 + 1/ox + 1/o2)
pm1, pmX, pm2 = (1/o1)/inv, (1/ox)/inv, (1/o2)/inv

# Real Stats Logic
alpha = min(1.0, total / 15)
h_wr = hw / h_t if h_t > 0 else pm1
a_wr = aw / a_t if a_t > 0 else pm2
p1 = alpha * h_wr + (1-alpha) * pm1
p2 = alpha * a_wr + (1-alpha) * pm2
pX = max(0.01, 1 - p1 - p2)
s_total = p1 + pX + p2
p1, pX, p2 = p1/s_total, pX/s_total, p2/s_total

# Value Check
v1, vX, v2 = p1 - pm1, pX - pmX, p2 - pm2
vals = {'1': v1, 'X': vX, '2': v2}
best_v_key = max(vals, key=vals.get)
edge = vals[best_v_key]
conf = int(min(100, (alpha * 55) + (max(0, edge) * 220)))

# --- HIERARCHY v17.0.7 με τις διορθώσεις σου ---
if pX < 0.15:
    res = "1" if p1 > p2 else "2"
    odd_check = o1 if res == "1" else o2
    if odd_check > 2.80: 
        base = f"{res} ({res}{'X' if res=='1' else '2'})" # π.χ. 1 (1X)
    else: 
        base = res
elif pX >= 0.40:
    base = "X"
elif abs(p1 - p2) < 0.12:
    base = "X"
else:
    res = best_v_key
    odd_check = o1 if res == "1" else o2
    if odd_check > 2.80:
        base = f"{res} ({res}{'X' if res=='1' else '2'})"
    else:
        base = res

# Προσθήκη κάλυψης αν χρειάζεται (Dominant point coverage)
if pX >= 0.15 and pX < 0.40 and abs(p1-p2) >= 0.12:
    if (hw + hd) > (aw + ad): base = f"{base} (1X)"
    else: base = f"{base} (X2)"

proposal = f"{base} (VALUE)"
color = "#2ecc71" if conf >= 75 else "#f1c40f" if conf >= 50 else "#e74c3c"

# Warnings
warning = ""
if total > 0 and (p1 + p2) < 0.40: 
    warning = "⚠️ HIGH RISK MATCH: Statistics are very low, abstention is recommended."
elif o1 <= 1.55 and pX > 0.28: 
    warning = "⚠️ ΠΑΓΙΔΑ ΣΤΟ Χ: Το φαβορί δυσκολεύεται στα στατιστικά."

# ==============================
# UI OUTPUT
# ==============================
st.markdown(f"""
<div class="result-card">
    <div style="color:gray;font-weight:bold;margin-bottom:5px;">REAL STATS ANALYSIS v17.0.7</div>
    <div style="font-size:3.5rem;font-weight:900;color:#1e3c72;line-height:1;">{proposal}</div>
    <div style="font-size:1.8rem;font-weight:bold;color:{color};margin-top:10px;">{conf}% Confidence</div>
</div>
""", unsafe_allow_html=True)

if warning: st.markdown(f'<div class="warning-box">{warning}</div>', unsafe_allow_html=True)

# Γράφημα
fig = go.Figure()
fig.add_trace(go.Bar(name='Bookie %', x=['1', 'X', '2'], y=[pm1*100, pmX*100, pm2*100], marker_color='#1e3c72'))
fig.add_trace(go.Bar(name='Real_Stats %', x=['1', 'X', '2'], y=[p1*100, pX*100, p2*100], marker_color='#2ecc71'))
fig.update_layout(barmode='group', height=350, margin=dict(l=20, r=20, t=20, b=20))
st.plotly_chart(fig, use_container_width=True)
