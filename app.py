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
    background: #ffffff; 
    padding: 1.5rem; 
    border-radius: 15px; 
    border: 2px solid #1e3c72; 
    text-align: center; 
    box-shadow: 0 4px 15px rgba(0,0,0,0.1); 
}
.main-proposal { 
    font-size: 3rem; 
    font-weight: 900; 
    color: #1e3c72; 
    line-height: 1.1; 
}
.coverage-text { 
    font-size: 1.8rem; 
    color: #555; 
    font-weight: 400; 
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
.stat-box {
    background-color: #f8f9fa;
    padding: 10px;
    border-radius: 8px;
    margin-top: 15px;
    font-family: monospace;
    font-size: 1rem;
    color: #555;
}
</style>
""", unsafe_allow_html=True)

# ==============================
# STATE INITIALIZATION
# ==============================
if 'hw' not in st.session_state:
    st.session_state.hw = 0
    st.session_state.hd = 0
    st.session_state.hl = 0
    st.session_state.aw = 0
    st.session_state.ad = 0
    st.session_state.al = 0

def reset_all():
    st.session_state.hw = 0
    st.session_state.hd = 0
    st.session_state.hl = 0
    st.session_state.aw = 0
    st.session_state.ad = 0
    st.session_state.al = 0

# ==============================
# SIDEBAR INPUTS
# ==============================
with st.sidebar:
    st.header("🏆 Control Panel")
    st.button("🧹 Clear Stats", on_click=reset_all, use_container_width=True)
    
    st.markdown("### 🏠 Γηπεδούχος (εντός έδρας)")
    st.number_input("Νίκες", 0, 100, key="hw", help="Νίκες σε όλους τους εντός έδρας αγώνες")
    st.number_input("Ισοπαλίες", 0, 100, key="hd", help="Ισοπαλίες σε όλους τους εντός έδρας αγώνες")
    st.number_input("Ήττες", 0, 100, key="hl", help="Ήττες σε όλους τους εντός έδρας αγώνες")
    
    st.markdown("### 🚀 Φιλοξενούμενος (εκτός έδρας)")
    st.number_input("Νίκες", 0, 100, key="aw", help="Νίκες σε όλους τους εκτός έδρας αγώνες")
    st.number_input("Ισοπαλίες", 0, 100, key="ad", help="Ισοπαλίες σε όλους τους εκτός έδρας αγώνες")
    st.number_input("Ήττες", 0, 100, key="al", help="Ήττες σε όλους τους εκτός έδρας αγώνες")

# ==============================
# LOGIC ENGINE
# ==============================
h_t = st.session_state.hw + st.session_state.hd + st.session_state.hl
a_t = st.session_state.aw + st.session_state.ad + st.session_state.al
total = h_t + a_t

# Αρχικοποίηση μεταβλητών
display_proposal = "📊 Αναμένοντας δεδομένα..."
conf = 0
color = "#95a5a6"
warning_msg = ""
real_1 = 0
real_X = 0
real_2 = 0

if total >= 6:
    # Υπολογισμός πραγματικών ποσοστών
    home_draw_pct = st.session_state.hd / h_t if h_t > 0 else 0
    away_draw_pct = st.session_state.ad / a_t if a_t > 0 else 0
    
    real_1 = st.session_state.hw / h_t if h_t > 0 else 0
    real_2 = st.session_state.aw / a_t if a_t > 0 else 0
    real_X = (home_draw_pct + away_draw_pct) / 2

    probs = {"1": real_1, "X": real_X, "2": real_2}
    base_point = max(probs, key=probs.get)
    
    # Καθορισμός Κυρίαρχου Σημείου
    display_proposal = base_point
    conf = int(probs[base_point] * 100)
    
    # Εφαρμογή Κανόνα Real Stat X < 15% -> Προσθήκη (1-2)
    if real_X < 0.15:
        display_proposal = f"{base_point} <span class='coverage-text'>(1-2)</span>"
        warning_msg = "🎯 ΚΑΘΟΛΟΥ ΙΣΟΠΑΛΙΑ: Το Χ είναι κάτω από 15%. Προτείνεται κάλυψη 1-2."
    else:
        # Αν δεν είναι 1-2, έλεγχος για άλλη απαραίτητη κάλυψη
        if base_point == "1" and real_X > 0.30:
            display_proposal = "1 <span class='coverage-text'>(1X)</span>"
            warning_msg = "🛡️ Υψηλό ποσοστό ισοπαλιών - Προτείνεται κάλυψη 1X"
        elif base_point == "2" and real_X > 0.30:
            display_proposal = "2 <span class='coverage-text'>(X2)</span>"
            warning_msg = "🛡️ Υψηλό ποσοστό ισοπαλιών - Προτείνεται κάλυψη X2"
    
    # Χρώμα confidence
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
        📊 Στατιστικά:<br>
        1: {real_1*100:.1f}% | X: {real_X*100:.1f}% | 2: {real_2*100:.1f}%
    </div>
</div>
""", unsafe_allow_html=True)

if warning_msg:
    st.markdown(f'<div class="warning-box">{warning_msg}</div>', unsafe_allow_html=True)

if total < 6:
    st.info("📊 Συμπληρώστε τουλάχιστον 6 συνολικά παιχνίδια για ανάλυση")
elif total < 10:
    st.warning("⚠️ ΜΕΙΩΜΕΝΗ ΑΞΙΟΠΙΣΤΙΑ: Λίγα στατιστικά δεδομένα (κάτω από 10 παιχνίδια)")

# ==============================
# STATS DISPLAY
# ==============================
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

# Footer
st.markdown("---")
st.caption("BetAnalyzer v17.2.9 - Απλή στατιστική ανάλυση με κάλυψη ισοπαλίας")
