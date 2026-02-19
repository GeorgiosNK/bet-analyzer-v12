import streamlit as st
import plotly.graph_objects as go
import streamlit.components.v1 as components

# ==============================
# CONFIG
# ==============================
st.set_page_config(page_title="BetAnalyzer v17.2.8", page_icon="⚽", layout="centered")

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
# PROFESSIONAL CSS
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
.dc-card {
    padding: 15px; border-radius: 10px; margin: 10px 0; 
    border-left: 5px solid;
    transition: transform 0.2s;
}
.dc-card:hover {
    transform: translateX(5px);
}
</style>
""", unsafe_allow_html=True)

# ==============================
# STATE INITIALIZATION (ΔΙΟΡΘΩΜΕΝΟ)
# ==============================
if 'hw' not in st.session_state:
    st.session_state.hw = 0
    st.session_state.hd = 0
    st.session_state.hl = 0
    st.session_state.aw = 0
    st.session_state.ad = 0
    st.session_state.al = 0

if 'o1' not in st.session_state:
    st.session_state.o1 = "1.00"
    st.session_state.ox = "1.00"
    st.session_state.o2 = "1.00"

if 'current_proposal' not in st.session_state:
    st.session_state.current_proposal = ""

def reset_all():
    st.session_state.hw = 0
    st.session_state.hd = 0
    st.session_state.hl = 0
    st.session_state.aw = 0
    st.session_state.ad = 0
    st.session_state.al = 0
    st.session_state.o1 = "1.00"
    st.session_state.ox = "1.00"
    st.session_state.o2 = "1.00"
    st.session_state.current_proposal = ""

# ==============================
# DOUBLE CHANCE ANALYSIS FUNCTIONS (ΔΙΟΡΘΩΜΕΝΟ)
# ==============================
def analyze_double_chance(p1, pX, p2, odd1, oddX, odd2, h_t, a_t, st_session):
    """
    Αναλύει αν αξίζει η διπλή ευκαιρία με έλεγχο απόδοσης
    """
    recommendations = []
    prob_1X = p1 + pX
    prob_X2 = pX + p2
    prob_12 = p1 + p2
    
    implied_1X = 1 / (1/odd1 + 1/oddX) if odd1 > 1.0 and oddX > 1.0 else 0
    implied_X2 = 1 / (1/oddX + 1/odd2) if oddX > 1.0 and odd2 > 1.0 else 0
    implied_12 = 1 / (1/odd1 + 1/odd2) if odd1 > 1.0 and odd2 > 1.0 else 0
    
    home_losses = st_session.hl if h_t > 0 else 1
    away_losses = st_session.al if a_t > 0 else 1

    # 1. Έλεγχος για 1X
    if implied_1X > 0:
        value = prob_1X - (1/implied_1X)
        # Ενσωμάτωση αλλαγής: Έλεγχος αήττητου ή υψηλού value/πιθανότητας
        if (home_losses == 0 and h_t >= 2) or (prob_1X > 0.65 and value > 0.02):
            risk = 'low' if prob_1X > 0.75 else 'medium'
            recommendations.append({
                'pick': '1X',
                'prob': prob_1X * 100,
                'odds': implied_1X,
                'value': value * 100,
                'risk': risk,
                'reason': "Γηπεδούχος αήττητος εντός έδρας - Ισχυρή στατιστική κάλυψη." if home_losses == 0 else f"Ελκυστική απόδοση {implied_1X:.2f} για {prob_1X*100:.0f}% πιθανότητα"
            })
    
    # 2. Έλεγχος για X2
    if implied_X2 > 0:
        value = prob_X2 - (1/implied_X2)
        if (away_losses == 0 and a_t >= 2) or (prob_X2 > 0.65 and value > 0.02):
            risk = 'low' if prob_X2 > 0.75 else 'medium'
            recommendations.append({
                'pick': 'X2',
                'prob': prob_X2 * 100,
                'odds': implied_X2,
                'value': value * 100,
                'risk': risk,
                'reason': "Φιλοξενούμενος αήττητος εκτός έδρας - Ισχυρή στατιστική κάλυψη." if away_losses == 0 else f"Ελκυστική απόδοση {implied_X2:.2f} για {prob_X2*100:.0f}% πιθανότητα"
            })
    
    # 3. Έλεγχος για 12
    if implied_12 > 0 and prob_12 > 0.80 and pX < 0.25:
        value = prob_12 - (1/implied_12)
        if value > 0.02:
            recommendations.append({
                'pick': '12',
                'prob': prob_12 * 100,
                'odds': implied_12,
                'value': value * 100,
                'risk': 'medium',
                'reason': f"Σχεδόν σίγουρο όχι ισοπαλία - {pX*100:.0f}% μόνο"
            })
    
    return recommendations

def get_double_chance_reason(p1, pX, p2, h_t, a_t, st_session):
    reasons = []
    if h_t > 0:
        home_l_rate = st_session.hl / h_t
        home_d_rate = st_session.hd / h_t
        if home_l_rate < 0.15: reasons.append(f"🏠 Γηπεδούχος: Μόνο {home_l_rate*100:.0f}% ήττες εντός έδρας")
        if home_d_rate > 0.35: reasons.append(f"🤝 Γηπεδούχος: {home_d_rate*100:.0f}% ισοπαλίες")
    if a_t > 0:
        away_l_rate = st_session.al / a_t
        away_d_rate = st_session.ad / a_t
        if away_l_rate < 0.20: reasons.append(f"🚀 Φιλοξενούμενος: Μόνο {away_l_rate*100:.0f}% ήττες εκτός έδρας")
        if away_d_rate > 0.35: reasons.append(f"🤝 Φιλοξενούμενος: {away_d_rate*100:.0f}% ισοπαλίες")
    return reasons

# ==============================
# FUNCTIONS FOR EXPLANATIONS
# ==============================
def generate_explanation(p1, pX, p2, odd1, oddX, odd2, h_t, a_t, st_session):
    explanation_parts = []
    if h_t > 0 and a_t > 0:
        h_pos = (st_session.hw + st_session.hd) / h_t
        a_pos = (st_session.aw + st_session.ad) / a_t
        if h_pos > 0.7: explanation_parts.append("🏠 **Ισχυρή εντός έδρας ομάδα**")
        elif a_pos > 0.7: explanation_parts.append("🚀 **Ισχυρή εκτός έδρας ομάδα**")
    if odd1 > 1.01 and (p1 > 0.5 and (1/odd1) < 0.4): explanation_parts.append(f"💰 **Value bet** στον Άσο")
    if odd2 > 1.01 and (p2 > 0.5 and (1/odd2) < 0.4): explanation_parts.append(f"💰 **Value bet** στο Διπλό")
    return explanation_parts

def calculate_key_metrics(p1, pX, p2, odd1, oddX, odd2):
    p1, pX, p2 = max(0.01, p1), max(0.01, pX), max(0.01, p2)
    implied_h = (1/odd1 * 100) if odd1 > 0 else 33
    implied_d = (1/oddX * 100) if oddX > 0 else 33
    implied_a = (1/odd2 * 100) if odd2 > 0 else 33
    metrics = {'home_edge': p1*100 - implied_h, 'draw_edge': pX*100 - implied_d, 'away_edge': p2*100 - implied_a}
    edges = [metrics['home_edge'], metrics['draw_edge'], metrics['away_edge']]
    metrics['best_value'] = ['home_edge', 'draw_edge', 'away_edge'][edges.index(max(edges))]
    metrics['value_amount'] = max(edges)
    return metrics

def get_risk_advice(p1, pX, p2, conf):
    if conf >= 70: return "🟢 **Υψηλή εμπιστοσύνη**: Κατάλληλο για κανονικό ποντάρισμα"
    elif conf >= 50: return "🟡 **Μέτρια εμπιστοσύνη**: Μείωση ποντάρισματος ή διπλή ευκαιρία"
    return "🔴 **Χαμηλή εμπιστοσύνη**: Μικρό ποντάρισμα ή αποφυγή"

def sf(x):
    try: return max(1.01, float(str(x).replace(',','.')))
    except: return 1.01

# ==============================
# SIDEBAR INPUTS
# ==============================
with st.sidebar:
    st.header("🏆 Control Panel")
    st.button("🧹 Clear Stats & Odds", on_click=reset_all, use_container_width=True)
    o1_i = st.text_input("Άσος (1)", key="o1")
    ox_i = st.text_input("Ισοπαλία (X)", key="ox")
    o2_i = st.text_input("Διπλό (2)", key="o2")

odd1, oddX, odd2 = sf(o1_i), sf(ox_i), sf(o2_i)

# ==============================
# CALCULATIONS ENGINE
# ==============================
h_t = st.session_state.hw + st.session_state.hd + st.session_state.hl
a_t = st.session_state.aw + st.session_state.ad + st.session_state.al
total = h_t + a_t

try:
    inv = (1/odd1 + 1/oddX + 1/odd2)
    pm1, pmX, pm2 = (1/odd1)/inv, (1/oddX)/inv, (1/odd2)/inv
except:
    pm1 = pmX = pm2 = 0.33

alpha = min(1.0, total / 15) if total > 0 else 0
h_wr = (st.session_state.hw - (st.session_state.hl * 0.3)) / h_t if h_t > 0 else pm1
a_wr = (st.session_state.aw - (st.session_state.al * 0.3)) / a_t if a_t > 0 else pm2

p1 = max(0.10, alpha * h_wr + (1-alpha) * pm1)
p2 = max(0.10, alpha * a_wr + (1-alpha) * pm2)
pX = max(0.01, 1 - p1 - p2)

s = p1 + pX + p2
p1, pX, p2 = p1/s, pX/s, p2/s

# ==============================
# FINAL LOGIC ENGINE
# ==============================
real_probs = {'1': p1, 'X': pX, '2': p2}
res = max(real_probs, key=real_probs.get)
conf = int(real_probs[res] * 100)
base = res

home_undefeated = (st.session_state.hl == 0 and h_t >= 2)
away_undefeated = (st.session_state.al == 0 and a_t >= 2)

if res == "2" and home_undefeated: base = "1X"
elif res == "1" and away_undefeated: base = "X2"

dc_recommendations = analyze_double_chance(p1, pX, p2, odd1, oddX, odd2, h_t, a_t, st.session_state)
if dc_recommendations:
    best_dc = max(dc_recommendations, key=lambda x: x['value'])
    if best_dc['value'] > 8 and best_dc['prob'] > 75 and best_dc['odds'] >= 1.40:
        base = best_dc['pick']

proposal = f"{base} (VALUE)"
st.session_state.current_proposal = proposal
color = "#2ecc71" if conf >= 65 else "#f1c40f" if conf >= 45 else "#e74c3c"

warning = ""
if total > 0 and (p1 + p2) < 0.40: warning = "⚠️ HIGH RISK MATCH: Statistics are very low, abstention is recommended."
elif odd1 <= 1.55 and pX > 0.28: warning = "⚠️ ΠΑΓΙΔΑ ΣΤΟ Χ: Το φαβορί δυσκολεύεται στα στατιστικά."

# ==============================
# UI OUTPUT
# ==============================
st.markdown(f"""
<div class="result-card">
    <div style="color:gray;font-weight:bold;margin-bottom:5px;">📊 BetAnalyzer v17.2.8</div>
    <div style="font-size:3.5rem;font-weight:900;color:#1e3c72;line-height:1;">{proposal}</div>
    <div style="font-size:1.8rem;font-weight:bold;color:{color};margin-top:10px;">{conf}% Confidence</div>
</div>
""", unsafe_allow_html=True)

if warning: st.markdown(f'<div class="warning-box">{warning}</div>', unsafe_allow_html=True)

# ==============================
# DOUBLE CHANCE ANALYSIS SECTION
# ==============================
with st.expander("🛡️ Double Chance Analysis", expanded=False):
    dc_recommendations = analyze_double_chance(p1, pX, p2, odd1, oddX, odd2, h_t, a_t, st.session_state)
    if dc_recommendations:
        for rec in dc_recommendations:
            bg_c = "#e8f5e9" if rec['odds'] >= 1.80 else "#fff3e0" if rec['odds'] >= 1.50 else "#e3f2fd"
            br_c = "#2ecc71" if rec['odds'] >= 1.80 else "#f39c12" if rec['odds'] >= 1.50 else "#3498db"
            v_c = "#2ecc71" if rec['value'] > 10 else "#f1c40f" if rec['value'] > 5 else "#95a5a6"
            risk_l = "🔴 Υψηλό" if rec['risk'] == 'high' else "🟡 Μέτριο" if rec['risk'] == 'medium' else "🟢 Χαμηλό"
            
            st.markdown(f"""
            <div class="dc-card" style="background-color: {bg_c}; border-left-color: {br_c};">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <span style="font-size: 2rem; font-weight: bold; color: #1e3c72;">{rec['pick']}</span>
                        <span style="font-size: 1.2rem; margin-left: 10px; background-color: white; padding: 3px 10px; border-radius: 15px;">{rec['prob']:.1f}%</span>
                    </div>
                    <div style="text-align: right;">
                        <div style="font-size: 1.8rem; font-weight: bold;">{rec['odds']:.2f}</div>
                        <div style="color: {v_c};">+{rec['value']:.1f}%</div>
                    </div>
                </div>
                <div style="margin-top: 10px; color: #34495e;">📌 {rec['reason']}</div>
                <div style="margin-top: 5px; font-size: 0.9rem;">Ρίσκο: {risk_l}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("ℹ️ Δεν εντοπίστηκαν ευκαιρίες double chance")

with st.expander("🔍 Αναλυτική Εξήγηση Πρόβλεψης", expanded=False):
    explanations = generate_explanation(p1, pX, p2, odd1, oddX, odd2, h_t, a_t, st.session_state)
    metrics = calculate_key_metrics(p1, pX, p2, odd1, oddX, odd2)
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 📋 Παράγοντες Πρόβλεψης")
        for exp in explanations[:3]: st.markdown(f"- {exp}")
    with col2:
        st.markdown("### ⚖️ Ανάλυση Value")
        st.markdown(f"✅ **Value detected**: +{metrics['value_amount']:.1f}%" if metrics['value_amount'] > 5 else "⚖️ **Fair value**")
    st.info(get_risk_advice(p1, pX, p2, conf))

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

# ==============================
# MAIN BAR CHART (ΑΠΕΙΡΑΧΤΟ)
# ==============================
fig = go.Figure()
fig.add_trace(go.Bar(name='Bookie %', x=['1', 'X', '2'], y=[pm1*100, pmX*100, pm2*100], marker_color='#1e3c72',
                     text=[f"<b>{pm1*100:.1f}%</b>", f"<b>{pmX*100:.1f}%</b>", f"<b>{pm2*100:.1f}%</b>"],
                     textposition='inside', textfont=dict(color="white", size=14)))
fig.add_trace(go.Bar(name='Real_Stats %', x=['1', 'X', '2'], y=[p1*100, pX*100, p2*100], marker_color='#2ecc71',
                     text=[f"<b>{p1*100:.1f}%</b>", f"<b>{pX*100:.1f}%</b>", f"<b>{p2*100:.1f}%</b>"],
                     textposition='inside', textfont=dict(color="white", size=14)))
fig.update_layout(barmode='group', height=350, xaxis=dict(type='category'), 
                  margin=dict(l=20, r=20, t=20, b=20),
                  legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
st.plotly_chart(fig, use_container_width=True)

st.caption("BetAnalyzer v17.2.8 - Double Chance Analysis Fix")
