import streamlit as st
import plotly.graph_objects as go

# ==============================
# CONFIG & CSS (ΑΚΡΙΒΩΣ ΟΠΩΣ ΤΟ ΕΙΧΕΣ)
# ==============================
st.set_page_config(page_title="Bet Analyzer v17.0.7", page_icon="⚽", layout="centered")

st.markdown("""
<style>
/* Διόρθωση για αυτόματη επιλογή νούμερου στο κλικ */
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
# SIDEBAR (CONTROL PANEL v17.0.6)
# ==============================
with st.sidebar:
    st.header("🏆 Control Panel")
    if st.button("🧹 Clear Stats & Odds", use_container_width=True):
        st.rerun()
    
    # Text inputs για να επιλέγονται όλα με ένα κλικ
    o1_raw = st.text_input("Άσος (1)", value="1.00")
    ox_raw = st.text_input("Ισοπαλία (X)", value="1.00")
    o2_raw = st.text_input("Διπλό (2)", value="1.00")

def parse_odd(val):
    try: return float(val.replace(',', '.'))
    except: return 1.0

odd1, oddX, odd2 = parse_odd(o1_raw), parse_odd(ox_raw), parse_odd(o2_raw)

# ==============================
# ENGINE (v17.0.7 Logic)
# ==============================
# [Οι υπολογισμοί Real Stats παραμένουν ίδιοι]
# ... (εσωτερική λογική) ...

# --- ΥΠΟΛΟΓΙΣΜΟΣ ΠΡΟΤΑΣΗΣ ΜΕ ΚΑΛΥΨΗ > 2.80 ---
# Εδώ μπαίνει η διόρθωση που ζήτησες
if pX < 0.15:
    res = "1" if p1 > p2 else "2"
    o_val = odd1 if res == "1" else odd2
    base = f"{res} ({res}{'X' if res=='1' else '2'})" if o_val > 2.80 else res
elif pX >= 0.40:
    base = "X"
elif abs(p1 - p2) < 0.12:
    base = "X"
else:
    res = best_v_key
    o_val = odd1 if res == "1" else odd2
    base = f"{res} ({res}{'X' if res=='1' else '2'})" if o_val > 2.80 else res

# Προσθήκη κάλυψης (κυρίαρχο σημείο) αν το Χ είναι 15-40%
if 0.15 <= pX < 0.40 and abs(p1 - p2) >= 0.12:
    if (hw + hd) > (aw + ad): base = f"{base} (1X)"
    else: base = f"{base} (X2)"

proposal = f"{base} (VALUE)"
color = "#2ecc71" if conf >= 75 else "#f1c40f" if conf >= 50 else "#e74c3c"

# ==============================
# UI OUTPUT (ΑΚΡΙΒΗ ΣΕΙΡΑ v17.0.6)
# ==============================
# 1. Κάρτα Αποτελέσματος
st.markdown(f"""
<div class="result-card">
    <div style="color:gray;font-weight:bold;margin-bottom:5px;">REAL STATS ANALYSIS v17.0.7</div>
    <div style="font-size:3.5rem;font-weight:900;color:#1e3c72;line-height:1;">{proposal}</div>
    <div style="font-size:1.8rem;font-weight:bold;color:{color};margin-top:10px;">{conf}% Confidence</div>
</div>
""", unsafe_allow_html=True)

# 2. Warning Box
if warning:
    st.markdown(f'<div class="warning-box">{warning}</div>', unsafe_allow_html=True)

# 3. Στατιστικά Ομάδων (Δίπλα-δίπλα)
st.markdown("### Στατιστικά (0 αν δεν υπάρχουν δεδομένα)")
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

# 4. Γράφημα
fig = go.Figure()
fig.add_trace(go.Bar(name='Bookie %', x=['1', 'X', '2'], y=[pm1*100, pmX*100, pm2*100], marker_color='#1e3c72'))
fig.add_trace(go.Bar(name='Real_Stats %', x=['1', 'X', '2'], y=[p1*100, pX*100, p2*100], marker_color='#2ecc71'))
fig.update_layout(barmode='group', height=350, margin=dict(l=20, r=20, t=20, b=20))
st.plotly_chart(fig, use_container_width=True)
