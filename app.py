import streamlit as st
import streamlit.components.v1 as components

# ==============================
# JS INPUT FIX (Auto-select & Comma to Dot)
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
# CONFIG & CSS
# ==============================
st.set_page_config(page_title="BetAnalyzer v17.2.9", page_icon="⚽", layout="centered")

st.markdown("""
<style>
.result-card { 
    background: #ffffff; padding: 1.5rem; border-radius: 15px; 
    border: 2px solid #1e3c72; text-align: center; 
    box-shadow: 0 4px 15px rgba(0,0,0,0.1); 
}
.main-proposal { 
    font-size: 3rem; font-weight: 900; color: #1e3c72; line-height: 1.1; 
}
.coverage-text { 
    font-size: 1.6rem; color: #cc0000; font-weight: bold; margin-left: 10px;
}
.warning-box { 
    background-color: #fff3cd; color: #856404; padding: 12px; 
    border-radius: 8px; border: 1px solid #ffeeba; margin: 10px 0; 
    font-weight: bold; text-align: center; 
}
.stat-box {
    background-color: #f8f9fa; padding: 10px; border-radius: 8px;
    margin-top: 15px; font-family: monospace; font-size: 1rem; color: #555;
}
.value-box {
    background-color: #e8f5e9; padding: 8px; border-radius: 8px;
    margin-top: 10px; font-size: 1rem; color: #2e7d32; border: 1px solid #a5d6a7;
}
</style>
""", unsafe_allow_html=True)

# ==============================
# STATE INITIALIZATION
# ==============================
for key in ['hw', 'hd', 'hl', 'aw', 'ad', 'al']:
    if key not in st.session_state: st.session_state[key] = 0

def reset_all():
    for key in ['hw', 'hd', 'hl', 'aw', 'ad', 'al']: st.session_state[key] = 0

# ==============================
# SIDEBAR INPUTS
# ==============================
with st.sidebar:
    st.header("🏆 Control Panel")
    st.button("🧹 Clear Stats", on_click=reset_all, use_container_width=True)
    
    st.markdown("### 💰 Αποδόσεις")
    o1 = st.number_input("Άσος (1)", 1.01, 50.0, 1.68, format="%.2f")
    ox = st.number_input("Ισοπαλία (X)", 1.01, 50.0, 3.75, format="%.2f")
    o2 = st.number_input("Διπλό (2)", 1.01, 50.0, 4.50, format="%.2f")

    st.markdown("---")
    st.markdown("### 🏠 Γηπεδούχος")
    st.number_input("Νίκες", 0, 100, key="hw")
    st.number_input("Ισοπαλίες", 0, 100, key="hd")
    st.number_input("Ήττες", 0, 100, key="hl")
    
    st.markdown("### 🚀 Φιλοξενούμενος")
    st.number_input("Νίκες", 0, 100, key="aw")
    st.number_input("Ισοπαλίες", 0, 100, key="ad")
    st.number_input("Ήττες", 0, 100, key="al")

# ==============================
# LOGIC ENGINE
# ==============================
h_t = st.session_state.hw + st.session_state.hd + st.session_state.hl
a_t = st.session_state.aw + st.session_state.ad + st.session_state.al
total = h_t + a_t

display_proposal = "📊 Αναμένοντας δεδομένα..."
conf = 0
color = "#95a5a6"
warning_msg = ""
value_text = ""
real_1, real_X, real_2 = 0, 0, 0

if total >= 6:
    # Υπολογισμός Real Stats
    real_1 = st.session_state.hw / h_t if h_t > 0 else 0
    real_2 = st.session_state.aw / a_t if a_t > 0 else 0
    # Το Real Stat X υπολογίζεται επί του συνόλου των αγώνων
    real_X = (st.session_state.hd + st.session_state.ad) / total if total > 0 else 0

    # Υπολογισμός Implied Probabilities από odds
    implied_1 = 1 / o1
    implied_X = 1 / ox
    implied_2 = 1 / o2
    implied_total = implied_1 + implied_X + implied_2
    
    # Κανονικοποίηση
    norm_implied_1 = implied_1 / implied_total * 100
    norm_implied_X = implied_X / implied_total * 100
    norm_implied_2 = implied_2 / implied_total * 100

    # Υπολογισμός Value
    value_1 = real_1 * 100 - norm_implied_1
    value_X = real_X * 100 - norm_implied_X
    value_2 = real_2 * 100 - norm_implied_2
    
    # Εύρεση best value
    values = {"1": value_1, "X": value_X, "2": value_2}
    best_value = max(values, key=values.get)
    
    if values[best_value] > 5:
        value_text = f"✅ **Value detected**: +{values[best_value]:.1f}% στο {best_value}"
    elif values[best_value] < -5:
        value_text = f"❌ **Overpriced**: {values[best_value]:.1f}% στο {best_value}"

    # Εύρεση κυρίαρχου σημείου
    probs = {"1": real_1, "X": real_X, "2": real_2}
    base_point = max(probs, key=probs.get)
    
    # Κανόνας Real Stat 1 & 2 > 45% ή Χ < 15% -> Αυτόματη πρόταση 1-2
    is_12_rule = (real_1 > 0.45 and real_2 > 0.45) or (real_X < 0.15)
    
    # Διαμόρφωση πρότασης με παρένθεση
    if is_12_rule:
        display_proposal = f"{base_point} (VALUE) <span class='coverage-text'>(1-2)</span>"
        warning_msg = "🎯 NO DRAW ALERT: Στατιστικά πολύ χαμηλό Χ. Προτίμηση στο 1-2."
    elif real_X > 0.40:
        display_proposal = f"X (VALUE)"
        warning_msg = "🤝 DRAW STRATEGY: Το Real Stat X είναι > 40%."
    else:
        # Έλεγχος για κλασικές καλύψεις
        if base_point == "1" and real_X > 0.25:
            display_proposal = f"1 (VALUE) <span class='coverage-text'>(1X)</span>"
            if not warning_msg:
                warning_msg = "🛡️ Υψηλό ποσοστό ισοπαλιών - Προτείνεται κάλυψη 1X"
        elif base_point == "2" and real_X > 0.25:
            display_proposal = f"2 (VALUE) <span class='coverage-text'>(X2)</span>"
            if not warning_msg:
                warning_msg = "🛡️ Υψηλό ποσοστό ισοπαλιών - Προτείνεται κάλυψη X2"
        else:
            display_proposal = f"{base_point} (VALUE)"

    conf = int(probs[base_point] * 100)
    color = "#2ecc71" if conf >= 65 else "#f1c40f" if conf >= 45 else "#e74c3c"

# ==============================
# UI OUTPUT
# ==============================
st.markdown(f"""
<div class="result-card">
    <div style="color:gray;font-weight:bold;margin-bottom:5px;">📊 BetAnalyzer v17.2.9</div>
    <div class="main-proposal">{display_proposal}</div>
    <div style="font-size:1.5rem;font-weight:bold;color:{color};margin-top:10px;">{conf}% Confidence</div>
    <div class="stat-box">
        📊 Στατιστικά: 1: {real_1*100:.1f}% | X: {real_X*100:.1f}% | 2: {real_2*100:.1f}%
    </div>
""", unsafe_allow_html=True)

if value_text:
    st.markdown(f'<div class="value-box">{value_text}</div>', unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

if warning_msg:
    st.markdown(f'<div class="warning-box">{warning_msg}</div>', unsafe_allow_html=True)

# Safety Net
if total >= 6 and (real_1 + real_2) < 0.40:
    st.error("⚠️ HIGH RISK MATCH: Statistics are very low, abstention is recommended.")

st.markdown("---")

# Εμφάνιση στατιστικών σε δύο στήλες
if total >= 6:
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 🏠 Γηπεδούχος")
        st.markdown(f"Νίκες: {st.session_state.hw}")
        st.markdown(f"Ισοπαλίες: {st.session_state.hd}")
        st.markdown(f"Ήττες: {st.session_state.hl}")
        st.markdown(f"**Σύνολο:** {h_t} αγώνες")
    
    with col2:
        st.markdown("### 🚀 Φιλοξενούμενος")
        st.markdown(f"Νίκες: {st.session_state.aw}")
        st.markdown(f"Ισοπαλίες: {st.session_state.ad}")
        st.markdown(f"Ήττες: {st.session_state.al}")
        st.markdown(f"**Σύνολο:** {a_t} αγώνες")
    
    # Εμφάνιση implied probabilities
    st.markdown("---")
    st.markdown("### 📈 Σύγκριση με Bookie")
    col3, col4, col5 = st.columns(3)
    with col3:
        st.metric("Άσος (1)", f"{norm_implied_1:.1f}%", f"{value_1:+.1f}%")
    with col4:
        st.metric("Ισοπαλία (X)", f"{norm_implied_X:.1f}%", f"{value_X:+.1f}%")
    with col5:
        st.metric("Διπλό (2)", f"{norm_implied_2:.1f}%", f"{value_2:+.1f}%")

if total < 6:
    st.info("📊 Συμπληρώστε τουλάχιστον 6 συνολικά παιχνίδια για ανάλυση")

# Footer
st.markdown("---")
st.caption("BetAnalyzer v17.2.9 - Στατιστική ανάλυση με κάλυψη ισοπαλίας και value detection")
