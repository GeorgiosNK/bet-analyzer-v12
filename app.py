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
real_1, real_X, real_2 = 0, 0, 0

if total >= 6:
    # 1. Real Stats
    real_1 = st.session_state.hw / h_t if h_t > 0 else 0
    real_2 = st.session_state.aw / a_t if a_t > 0 else 0
    real_X = (st.session_state.hd + st.session_state.ad) / total if total > 0 else 0

    # 2. Value Calculation
    implied_total = (1/o1) + (1/ox) + (1/o2)
    norm_impl_1 = (1/o1) / implied_total * 100
    norm_impl_2 = (1/o2) / implied_total * 100
    norm_impl_X = (1/ox) / implied_total * 100

    # 3. Dominant Point
    probs = {"1": real_1, "X": real_X, "2": real_2}
    base_point = max(probs, key=probs.get)
    
    main_text = base_point
    # Value flag logic
    current_real = probs[base_point] * 100
    current_implied = norm_impl_1 if base_point == "1" else norm_impl_X if base_point == "X" else norm_impl_2
    if current_real > current_implied:
        main_text += " (VALUE)"

    # 4. Coverage Logic
    coverage_html = ""
    is_12_rule = (real_1 > 0.45 and real_2 > 0.45) or (real_X < 0.15)
    
    if is_12_rule:
        coverage_html = f" <span class='coverage-text'>(1-2)</span>"
        warning_msg = "🎯 NO DRAW ALERT: Το Χ είναι κάτω από 15%. Προτείνεται 1-2."
    elif real_X > 0.40:
        main_text = "X (VALUE)"
        warning_msg = "🤝 DRAW STRATEGY: Real Stat X > 40%."
    elif base_point == "1" and real_X > 0.25:
        coverage_html = f" <span class='coverage-text'>(1X)</span>"
    elif base_point == "2" and real_X > 0.25:
        coverage_html = f" <span class='coverage-text'>(X2)</span>"

    display_proposal = f"{main_text}{coverage_html}"
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
        [LIVE PROBS]: 1: {real_1*100:.1f}% | X: {real_X*100:.1f}% | 2: {real_2*100:.1f}%
    </div>
</div>
""", unsafe_allow_html=True)

if warning_msg:
    st.markdown(f'<div class="warning-box">{warning_msg}</div>', unsafe_allow_html=True)

if total >= 6 and (real_1 + real_2) < 0.40:
    st.error("⚠️ HIGH RISK MATCH: Statistics are very low, abstention is recommended.")

st.markdown("---")
if total < 6:
    st.info("📊 Συμπληρώστε τουλάχιστον 6 συνολικά παιχνίδια για ανάλυση")
