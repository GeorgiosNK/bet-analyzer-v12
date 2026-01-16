import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import streamlit.components.v1 as components

# ==============================
# CONFIG & PROFESSIONAL CSS 
# ==============================
st.set_page_config(page_title="Bet Analyzer v12.13.3.8 PRO", page_icon="⚽", layout="centered")

# SMART JAVASCRIPT FIX: Auto-select, Comma-to-Dot & NUMPAD ACTIVATION
components.html(
    """
    <script>
        const setupInputs = () => {
            const inputs = window.parent.document.querySelectorAll('input');
            inputs.forEach(input => {
                // Auto-select on focus
                input.addEventListener('focus', function() { this.select(); });
                
                // Trigger Numpad on Mobile
                input.setAttribute('inputmode', 'decimal');

                // Smart Comma to Dot conversion
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
    """,
    height=0,
)

st.markdown("""
<style>
    [data-testid="stVerticalBlock"] > div:has(div.sticky-result) {
        position: sticky; top: 2.8rem; z-index: 1000;
        background: rgba(240, 242, 246, 0.98); padding-bottom: 10px;
    }
    .result-card {
        background: #ffffff; padding: 1rem; border-radius: 15px;
        border: 2px solid #1e3c72; box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        text-align: center;
    }
    .conf-bar { height: 24px; border-radius: 12px; background: #f0f2f6; overflow: hidden; position: relative; border: 1px solid #ddd; }
    .conf-fill { height: 100%; transition: width 0.8s ease-in-out; }
    .info-text {
        background-color: #e8f0fe; padding: 15px; border-radius: 10px;
        border-left: 5px solid #1e3c72; margin-bottom: 20px; font-size: 0.95rem;
    }
    .warning-box {
        background-color: #fff3cd; color: #856404; padding: 12px; 
        border-radius: 8px; border: 1px solid #ffeeba; margin-top: 10px; 
        font-weight: bold; text-align: center; font-size: 0.9rem;
    }
    .pos-badge {
        background: #1e3c72; color: white; padding: 2px 8px; 
        border-radius: 5px; font-size: 0.85rem; margin-left: 10px;
    }
    .guide-item { padding: 12px; margin: 10px 0; border-radius: 8px; font-size: 0.9rem; }
</style>
""", unsafe_allow_html=True)

# APP INFO TEXT - ΣΤΑΘΕΡΟ ΛΕΚΤΙΚΟ
st.markdown("""
<div class="info-text">
    <strong>⚽ Bet Analyzer Pro</strong><br>
    Ο Bet Analyzer είναι μια προηγμένη εφαρμογή ανάλυσης ποδοσφαιρικών αναμετρήσεων που συνδυάζει τα δεδομένα της στοιχηματικής αγοράς (Market Odds) με τα πραγματικά στατιστικά επιδόσεων των ομάδων (Real Stats).
</div>
""", unsafe_allow_html=True)

# ==============================
# INITIALIZATION & RESET LOGIC
# ==============================
if 'hw' not in st.session_state:
    st.session_state.update({'hw':0, 'hd':0, 'hl':0, 'aw':0, 'ad':0, 'al':0})

if 'o1_str' not in st.session_state:
    st.session_state.update({'o1_str': "1.00", 'ox_str': "1.00", 'o2_str': "1.00"})

def reset_everything():
    for k in ['hw','hd','hl','aw','ad','al']: 
        st.session_state[k] = 0
    st.session_state.o1_str = "1.00"
    st.session_state.ox_str = "1.00"
    st.session_state.o2_str = "1.00"

# ==============================
# SIDEBAR
# ==============================
with st.sidebar:
    st.markdown("### 🏆 Bet Analyzer Pro")
    st.caption("Version 12.13.3.8 PRO")
    st.divider()
    st.button("🧹 Clear All Stats & Odds", on_click=reset_everything, use_container_width=True)
    
    st.header("📊 Αποδόσεις (Odds)")
    o1_input = st.text_input("Άσος (1)", key="o1_str")
    ox_input = st.text_input("Ισοπαλία (X)", key="ox_str")
    o2_input = st.text_input("Διπλό (2)", key="o2_str")

def safe_float(val):
    try: return float(str(val).replace(',', '.'))
    except: return 1.00

ace_odds = max(1.0, safe_float(o1_input))
draw_odds = max(1.0, safe_float(ox_input))
double_odds = max(1.0, safe_float(o2_input))

# ==============================
# LOGIC ENGINE
# ==============================
h_total = st.session_state.hw + st.session_state.hd + st.session_state.hl
a_total = st.session_state.aw + st.session_state.ad + st.session_state.al
total_all = h_total + a_total
is_blind = (total_all == 0)

inv_odds = (1/ace_odds + 1/draw_odds + 1/double_odds)
prob_1, prob_X, prob_2 = (1/ace_odds)/inv_odds, (1/draw_odds)/inv_odds, (1/double_odds)/inv_odds

h_pos = (st.session_state.hw + st.session_state.hd)/h_total if h_total > 0 else 0
a_pos = (st.session_state.aw + st.session_state.ad)/a_total if a_total > 0 else 0

warning_msg = ""
proposal = ""

if is_blind:
    real_1, real_X, real_2 = prob_1, prob_X, prob_2
    mode_label = "⚖️ BLIND MODE • ΠΡΟΤΑΣΗ"
    proposal = "1 (1X)" if prob_1 >= prob_2 else "2 (X2)"
else:
    real_1 = st.session_state.hw/h_total if h_total > 0 else 0
    real_X = (st.session_state.hd + st.session_state.ad)/total_all if total_all > 0 else 0
    real_2 = st.session_state.aw/a_total if a_total > 0 else 0
    mode_label = "⚖️ ΣΤΑΤΙΣΤΙΚΗ ΥΠΕΡΟΧΗ • ΠΡΟΤΑΣΗ"

    if real_X >= 0.40:
        if a_pos >= 2 * h_pos and a_pos > 0: proposal = "X (X2)"
        else: proposal = "X (1X)"
    elif real_X < 0.15:
        main = "1" if real_1 >= real_2 else "2"
        proposal = f"{main} (1-2)"
    elif real_1 > 0.45 and real_2 > 0.45:
        proposal = "1 (1-2)"
    elif a_pos >= 2 * h_pos and a_pos > 0:
        proposal = "2 (X2)"
    elif h_pos >= 2 * a_pos and h_pos > 0:
        proposal = "1 (1X)"
    else:
        proposal = "1 (1X)" if h_pos >= a_pos else "2 (X2)"

    if (real_1 + real_2) < 0.40:
        warning_msg = "⚠️ ΑΓΩΝΑΣ ΥΨΗΛΟΥ ΚΙΝΔΥΝΟΥ: Τα στατιστικά στοιχεία είναι πολύ χαμηλά, συνιστάται η αποχή."
        mode_label += " (Low Confidence)"
    
    if ace_odds <= 1.50 and real_X > 0.25:
        warning_msg = "⚠️ ΠΑΓΙΔΑ στο Χ: Ένδειξη ότι το φαβορί θα δυσκολευτεί."

confidence = max(5, min(100, int((1 - abs(real_1 - prob_1) - abs(real_2 - prob_2)) * 100)))

if confidence >= 80: color = "#2ecc71"
elif confidence >= 60: color = "#f1c40f"
else: color = "#e74c3c"

# ==============================
# STICKY HEADER & RESULTS
# ==============================
st.markdown(f"""
<div class="sticky-result">
<div class="result-card">
<div style="font-size: 0.75rem; color: #666; font-weight:bold; margin-bottom: 2px;">{mode_label}</div>
<div style="font-size: 3.5rem; font-weight: 900; color: #1e3c72; line-height: 1; margin: 0;">{proposal}</div>
<div style="font-size: 1.6rem; font-weight: 900; color: {color}; margin-bottom: 10px;">{confidence}%</div>
<div style="max-width: 550px; margin: 0 auto;">
<div style="width: 100%; height: 32px; background: #f0f2f6; position: relative; border-radius: 166px; border: 1px solid #ddd; overflow: hidden; box-shadow: inset 0 1px 3px rgba(0,0,0,0.1);">
<div style="width: {confidence}%; background: {color}; height: 100%; transition: width 0.8s ease-in-out;"></div>
<div style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; display: flex; align-items: center; justify-content: center;">
<span style="color: white; font-weight: 900; font-size: 1rem; letter-spacing: 1.5px; 
text-shadow: -1px -1px 0 #000, 1px -1px 0 #000, -1px 1px 0 #000, 1px 1px 0 #000, 2px 2px 4px rgba(0,0,0,0.5);">
CONFIDENCE BAR
</span>
</div>
</div>
</div>
</div>
</div>
""", unsafe_allow_html=True)

if warning_msg:
    st.markdown(f'<div class="warning-box">{warning_msg}</div>', unsafe_allow_html=True)

# ==============================
# MAIN INPUTS
# ==============================
st.markdown("### 📝 Στατιστικά Ομάδων")
c1, c2 = st.columns(2)
with c1:
    st.markdown(f'**🏠 Γηπεδούχος** <span class="pos-badge">{h_pos*100:.1f}% Positive</span>', unsafe_allow_html=True)
    st.number_input("Εντός_Νίκες", 0, 100, key="hw")
    st.number_input("Εντός_Ισοπαλίες", 0, 100, key="hd")
    st.number_input("Εντός_Ήττες", 0, 100, key="hl")
with c2:
    st.markdown(f'**🚀 Φιλοξενούμενος** <span class="pos-badge">{a_pos*100:.1f}% Positive</span>', unsafe_allow_html=True)
    st.number_input("Εκτός_Νίκες (A)", 0, 100, key="aw")
    st.number_input("Εκτός_Ισοπαλίες (A)", 0, 100, key="ad")
    st.number_input("Εκτός_Ήττες (A)", 0, 100, key="al")

# ==============================
# TABS
# ==============================
tab1, tab2 = st.tabs(["📊 Ανάλυση & Γράφημα", "🛡️ Οδηγός Στρατηγικής"])

with tab1:
    fig = go.Figure()
    x_labels = ["1", "X", "2"]
    # Booker Bar με Bold Λευκά Νούμερα
    fig.add_trace(go.Bar(
        name='Booker_Odds', x=x_labels, y=[prob_1*100, prob_X*100, prob_2*100], 
        marker_color='#FF4B4B', 
        text=[f"<b>{prob_1*100:.1f}%</b>", f"<b>{prob_X*100:.1f}%</b>", f"<b>{prob_2*100:.1f}%</b>"], 
        textposition='inside', insidetextfont=dict(color='white')
    ))
    # Performance Bar με Bold Λευκά Νούμερα
    fig.add_trace(go.Bar(
        name='Performance_Stats', x=x_labels, y=[real_1*100, real_X*100, real_2*100], 
        marker_color='#0083B0', 
        text=[f"<b>{real_1*100:.1f}%</b>", f"<b>{real_X*100:.1f}%</b>", f"<b>{real_2*100:.1f}%</b>"], 
        textposition='inside', insidetextfont=dict(color='white')
    ))
    fig.update_layout(
        barmode='group', height=350, margin=dict(l=10, r=10, t=10, b=10),
        xaxis=dict(type='category'), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.markdown("""
    <div class="guide-item" style="border-left: 5px solid #2ecc71; background: rgba(46, 204, 113, 0.1);">
        <strong style="color: #2ecc71;">Confidence >80% (Πράσινο):</strong><br>
        Θεώρησέ το ως την "Κύρια Επιλογή" σου. Είναι τα ματς όπου η στατιστική "ασφάλεια" είναι στο μέγιστο επίπεδο.
    </div>
    <div class="guide-item" style="border-left: 5px solid #f1c40f; background: rgba(241, 196, 15, 0.1);">
        <strong style="color: #d4ac0d;">Confidence 61-79% (Κίτρινο/Πορτοκαλί):</strong><br>
        Είναι τα ματς για "κάλυψη" (π.χ. αν προτείνει 1, ίσως το 1Χ να είναι πιο σοφό) ή για μικρότερο ποντάρισμα.
    </div>
    <div class="guide-item" style="border-left: 5px solid #e74c3c; background: rgba(231, 76, 60, 0.1);">
        <strong style="color: #e74c3c;">Confidence <=60% (Κόκκινο):</strong><br>
        Ακόμα και αν η πρόταση φαίνεται ελκυστική, το μοντέλο σε προειδοποιεί ότι το ματς είναι "τζόγος".
    </div>
    """, unsafe_allow_html=True)
