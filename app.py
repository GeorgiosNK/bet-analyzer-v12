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
# STATE INITIALIZATION
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
# DOUBLE CHANCE ANALYSIS FUNCTIONS
# ==============================
def analyze_double_chance(p1, pX, p2, odd1, oddX, odd2, h_t, a_t, st_session):
    """
    Αναλύει αν αξίζει η διπλή ευκαιρία με έλεγχο απόδοσης
    """
    recommendations = []
    
    # Υπολογισμός πιθανοτήτων για double chance
    prob_1X = p1 + pX
    prob_X2 = pX + p2
    prob_12 = p1 + p2
    
    # Υπολογισμός αποδόσεων double chance
    implied_1X = 1 / (1/odd1 + 1/oddX) if odd1 > 1.0 and oddX > 1.0 else 0
    implied_X2 = 1 / (1/oddX + 1/odd2) if oddX > 1.0 and odd2 > 1.0 else 0
    implied_12 = 1 / (1/odd1 + 1/odd2) if odd1 > 1.0 and odd2 > 1.0 else 0
    
    # Στατιστικά στοιχεία
    if h_t > 0:
        home_losses = st_session.hl / h_t
        home_draws = st_session.hd / h_t
    else:
        home_losses = home_draws = 0.5
    
    if a_t > 0:
        away_losses = st_session.al / a_t
        away_draws = st_session.ad / a_t
    else:
        away_losses = away_draws = 0.5
    
    # 1. Έλεγχος για 1X (Γηπεδούχος ή Ισοπαλία)
    if implied_1X > 0 and prob_1X > 0.65:
        value = prob_1X - (1/implied_1X)
        
        if implied_1X >= 1.80 and value > 0.03:
            recommendations.append({
                'pick': '1X',
                'prob': prob_1X * 100,
                'odds': implied_1X,
                'value': value * 100,
                'risk': 'high',
                'reason': f"Ελκυστική απόδοση {implied_1X:.2f} για {prob_1X*100:.0f}% πιθανότητα"
            })
        elif implied_1X >= 1.50 and value > 0.05 and home_losses < 0.25:
            recommendations.append({
                'pick': '1X',
                'prob': prob_1X * 100,
                'odds': implied_1X,
                'value': value * 100,
                'risk': 'medium',
                'reason': f"Γηπεδούχος αήττητος σε {prob_1X*100:.0f}% (χάνει μόνο {home_losses*100:.0f}%)"
            })
        elif implied_1X >= 1.30 and prob_1X > 0.75 and home_losses < 0.15:
            recommendations.append({
                'pick': '1X',
                'prob': prob_1X * 100,
                'odds': implied_1X,
                'value': value * 100,
                'risk': 'low',
                'reason': f"Πολύ ασφαλές 1X - {prob_1X*100:.0f}% πιθανότητα"
            })
    
    # 2. Έλεγχος για X2 (Φιλοξενούμενος ή Ισοπαλία)
    if implied_X2 > 0 and prob_X2 > 0.65:
        value = prob_X2 - (1/implied_X2)
        
        if implied_X2 >= 1.80 and value > 0.03:
            recommendations.append({
                'pick': 'X2',
                'prob': prob_X2 * 100,
                'odds': implied_X2,
                'value': value * 100,
                'risk': 'high',
                'reason': f"Ελκυστική απόδοση {implied_X2:.2f} για {prob_X2*100:.0f}% πιθανότητα"
            })
        elif implied_X2 >= 1.50 and value > 0.05 and away_losses < 0.30:
            recommendations.append({
                'pick': 'X2',
                'prob': prob_X2 * 100,
                'odds': implied_X2,
                'value': value * 100,
                'risk': 'medium',
                'reason': f"Φιλοξενούμενος αήττητος σε {prob_X2*100:.0f}% (χάνει μόνο {away_losses*100:.0f}%)"
            })
        elif implied_X2 >= 1.30 and prob_X2 > 0.75 and away_losses < 0.20:
            recommendations.append({
                'pick': 'X2',
                'prob': prob_X2 * 100,
                'odds': implied_X2,
                'value': value * 100,
                'risk': 'low',
                'reason': f"Πολύ ασφαλές X2 - {prob_X2*100:.0f}% πιθανότητα"
            })
    
    # 3. Έλεγχος για 12 (Όχι ισοπαλία)
    if implied_12 > 0 and prob_12 > 0.80 and pX < 0.25:
        value = prob_12 - (1/implied_12)
        
        if implied_12 >= 1.40 and value > 0.02:
            risk = 'low' if prob_12 > 0.90 else 'medium'
            recommendations.append({
                'pick': '12',
                'prob': prob_12 * 100,
                'odds': implied_12,
                'value': value * 100,
                'risk': risk,
                'reason': f"Σχεδόν σίγουρο όχι ισοπαλία - {pX*100:.0f}% μόνο"
            })
    
    return recommendations

def get_double_chance_reason(p1, pX, p2, h_t, a_t, st_session):
    """
    Επιστρέφει στατιστικούς λόγους για double chance
    """
    reasons = []
    
    if h_t > 0:
        home_losses = st_session.hl / h_t
        home_draws = st_session.hd / h_t
        if home_losses < 0.15:
            reasons.append(f"🏠 Γηπεδούχος: Μόνο {home_losses*100:.0f}% ήττες εντός έδρας")
        if home_draws > 0.35:
            reasons.append(f"🤝 Γηπεδούχος: {home_draws*100:.0f}% ισοπαλίες")
    
    if a_t > 0:
        away_losses = st_session.al / a_t
        away_draws = st_session.ad / a_t
        if away_losses < 0.20:
            reasons.append(f"🚀 Φιλοξενούμενος: Μόνο {away_losses*100:.0f}% ήττες εκτός έδρας")
        if away_draws > 0.35:
            reasons.append(f"🤝 Φιλοξενούμενος: {away_draws*100:.0f}% ισοπαλίες")
    
    if pX < 0.20:
        reasons.append(f"⚡ Πολύ λίγες ισοπαλίες ({pX*100:.0f}%) - Ψάξε για 12")
    elif pX > 0.35:
        reasons.append(f"⚠️ Υψηλό ποσοστό ισοπαλιών ({pX*100:.0f}%) - Προσοχή")
    
    return reasons

# ==============================
# FUNCTIONS FOR EXPLANATIONS
# ==============================
def generate_explanation(p1, pX, p2, odd1, oddX, odd2, h_t, a_t, st_session):
    """
    Δημιουργεί αναλυτική εξήγηση για την πρόταση
    """
    explanation_parts = []
    
    # 1. Ανάλυση στατιστικών
    if h_t > 0 and a_t > 0:
        h_pos = (st_session.hw + st_session.hd) / h_t
        a_pos = (st_session.aw + st_session.ad) / a_t
        
        if h_pos > 0.7:
            explanation_parts.append("🏠 **Ισχυρή εντός έδρας ομάδα**: Η γηπεδούχος έχει πολύ καλή φόρμα")
        elif a_pos > 0.7:
            explanation_parts.append("🚀 **Ισχυρή εκτός έδρας ομάδα**: Η φιλοξενούμενη έχει πολύ καλή φόρμα")
        
        if h_t > 0 and st_session.hw > st_session.hl * 2:
            explanation_parts.append("⚽ **Επιθετικό πλεονέκτημα**: Η γηπεδούχος σκοράρει συχνά")
        
        if a_t > 0 and st_session.aw > st_session.al * 2:
            explanation_parts.append("⚽ **Επιθετικό πλεονέκτημα**: Η φιλοξενούμενη σκοράρει συχνά")
    
    # 2. Ανάλυση αποδόσεων
    if odd1 > 1.01:
        implied_home = 1/odd1 * 100
        if implied_home < 40 and p1 > 0.5:
            explanation_parts.append(f"💰 **Value bet**: Η απόδοση {odd1:.2f} είναι υψηλή για {p1*100:.0f}% πιθανότητα")
    
    if odd2 > 1.01:
        implied_away = 1/odd2 * 100
        if implied_away < 40 and p2 > 0.5:
            explanation_parts.append(f"💰 **Value bet**: Η απόδοση {odd2:.2f} είναι υψηλή για {p2*100:.0f}% πιθανότητα")
    
    # 3. Ανάλυση Χ (ισοπαλίας)
    if oddX > 1.01:
        implied_draw = 1/oddX * 100
        if pX > 0.35:
            explanation_parts.append(f"🤝 **Υψηλή πιθανότητα ισοπαλίας**: {pX*100:.0f}% - Προσοχή στο Χ")
        elif pX < 0.20:
            explanation_parts.append("⚡ **Χαμηλό Χ**: Οι ομάδες δεν ισοπαλούν συχνά")
    
    # 4. Εξήγηση τελικής πρότασης
    proposal = st_session.get('current_proposal', '')
    
    if "1X" in proposal:
        explanation_parts.append("🛡️ **Κάλυψη**: Προτείνεται διπλή ευκαιρία 1X λόγω στατιστικών")
    elif "X2" in proposal:
        explanation_parts.append("🛡️ **Κάλυψη**: Προτείνεται διπλή ευκαιρία X2 λόγω στατιστικών")
    
    if proposal == "1 (VALUE)":
        explanation_parts.append("✅ **Καθαρό φαβορί**: Η γηπεδούχος υπερέχει στατιστικά")
    elif proposal == "2 (VALUE)":
        explanation_parts.append("✅ **Καθαρό φαβορί**: Η φιλοξενούμενη υπερέχει στατιστικά")
    elif proposal == "X (VALUE)":
        explanation_parts.append("⚠️ **Ισοπαλία**: Οι ομάδες είναι πολύ κοντά ή υπάρχει αμυντική τακτική")
    
    return explanation_parts

def calculate_key_metrics(p1, pX, p2, odd1, oddX, odd2):
    """
    Υπολογίζει βασικές μετρικές για σύγκριση
    """
    # Εξασφαλίζουμε ότι όλες οι τιμές είναι έγκυρες
    p1 = max(0.01, min(0.99, p1)) if isinstance(p1, (int, float)) else 0.33
    pX = max(0.01, min(0.99, pX)) if isinstance(pX, (int, float)) else 0.33
    p2 = max(0.01, min(0.99, p2)) if isinstance(p2, (int, float)) else 0.33
    
    odd1 = max(1.01, odd1) if isinstance(odd1, (int, float)) and odd1 > 0 else 2.0
    oddX = max(1.01, oddX) if isinstance(oddX, (int, float)) and oddX > 0 else 2.0
    odd2 = max(1.01, odd2) if isinstance(odd2, (int, float)) and odd2 > 0 else 2.0
    
    # Ασφαλής υπολογισμός implied probabilities
    implied_home = (1/odd1 * 100)
    implied_draw = (1/oddX * 100)
    implied_away = (1/odd2 * 100)
    
    # Κανονικοποίηση
    total_implied = implied_home + implied_draw + implied_away
    if total_implied > 0:
        implied_home = (implied_home / total_implied) * 100
        implied_draw = (implied_draw / total_implied) * 100
        implied_away = (implied_away / total_implied) * 100
    
    # Υπολογισμός edges
    home_edge = p1 * 100 - implied_home
    draw_edge = pX * 100 - implied_draw
    away_edge = p2 * 100 - implied_away
    
    # Δημιουργία dictionary
    metrics = {
        'home_edge': home_edge,
        'draw_edge': draw_edge,
        'away_edge': away_edge
    }
    
    # Εύρεση best value
    edges = [home_edge, draw_edge, away_edge]
    edge_names = ['home_edge', 'draw_edge', 'away_edge']
    
    if edges:
        max_edge = max(edges)
        max_index = edges.index(max_edge)
        metrics['best_value'] = edge_names[max_index]
        metrics['value_amount'] = max_edge
    else:
        metrics['best_value'] = 'home_edge'
        metrics['value_amount'] = 0
    
    return metrics

def get_risk_advice(p1, pX, p2, conf):
    """
    Επιστρέφει συμβουλές διαχείρισης ρίσκου
    """
    if conf >= 70:
        return "🟢 **Υψηλή εμπιστοσύνη**: Κατάλληλο για κανονικό ποντάρισμα"
    elif conf >= 50:
        return "🟡 **Μέτρια εμπιστοσύνη**: Μείωση ποντάρισματος ή διπλή ευκαιρία"
    else:
        return "🔴 **Χαμηλή εμπιστοσύνη**: Μικρό ποντάρισμα ή αποφυγή"

# ==============================
# SAFE FUNCTION FOR ODDS
# ==============================
def sf(x):
    """Ασφαλής μετατροπή odds"""
    try: 
        v = float(str(x).replace(',','.'))
        return max(1.01, v)
    except: 
        return 1.01

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
# CALCULATIONS ENGINE (ΔΙΟΡΘΩΜΕΝΟ ΜΕ ΑΥΣΤΗΡΟΤΕΡΟ LOSS PENALTY)
# ==============================
h_t = st.session_state.hw + st.session_state.hd + st.session_state.hl
a_t = st.session_state.aw + st.session_state.ad + st.session_state.al
total = h_t + a_t

# Ασφαλής υπολογισμός implied probabilities
try:
    inv = (1/odd1 + 1/oddX + 1/odd2)
    if inv > 0:
        pm1, pmX, pm2 = (1/odd1)/inv, (1/oddX)/inv, (1/odd2)/inv
    else:
        pm1 = pmX = pm2 = 0.33
except:
    pm1 = pmX = pm2 = 0.33

alpha = min(1.0, total / 15) if total > 0 else 0

# ΑΥΣΤΗΡΟΤΕΡΟ LOSS PENALTY (0.5 αντί για 0.3)
loss_penalty = 0.5

# Υπολογισμός win ratios με αυστηρότερο penalty
h_wr = (st.session_state.hw - (st.session_state.hl * loss_penalty)) / h_t if h_t > 0 else pm1
a_wr = (st.session_state.aw - (st.session_state.al * loss_penalty)) / a_t if a_t > 0 else pm2

# ΜΠΟΝΟΥΣ ΓΙΑ ΑΗΤΤΗΤΟ (μόνο αν έχει παίξει τουλάχιστον 3 ματς)
if h_t >= 3 and st.session_state.hl == 0:
    h_wr = h_wr * 1.2  # 20% μπόνους στην γηπεδούχο

if a_t >= 3 and st.session_state.al == 0:
    a_wr = a_wr * 1.2  # 20% μπόνους στην φιλοξενούμενη

# Υπολογισμός πιθανοτήτων
p1 = alpha * h_wr + (1-alpha) * pm1
p2 = alpha * a_wr + (1-alpha) * pm2

p1, p2 = max(0.10, p1), max(0.10, p2)
pX = max(0.01, 1 - p1 - p2)

# ΕΠΙΠΛΕΟΝ ΕΛΕΓΧΟΣ: Αν η γηπεδούχος είναι αήττητη και το μοντέλο προτείνει διπλό
if h_t >= 3 and st.session_state.hl == 0 and p2 > p1:
    # Μείωσε δραστικά την πιθανότητα του διπλού
    p2 = p2 * 0.5  # Μείωση 50%
    # Ανακατένειμε στις άλλες επιλογές
    remaining = 1 - p2
    if remaining > 0:
        p1 = p1 / (p1 + pX) * remaining
        pX = pX / (p1 + pX) * remaining

real_h_draw = st.session_state.hd / h_t if h_t > 0 else 0.25
real_a_draw = st.session_state.ad / a_t if a_t > 0 else 0.25
avg_draw = (real_h_draw + real_a_draw) / 2

# Draw Normalization
if pX > 0.50 and avg_draw < 0.40:
    diff = pX - 0.50
    p1 += diff * 0.5
    p2 += diff * 0.5
    pX = 0.50

s = p1 + pX + p2
if s > 0:
    p1, pX, p2 = p1/s, pX/s, p2/s

# ==============================
# FINAL LOGIC ENGINE
# ==============================
real_probs = {'1': p1, 'X': pX, '2': p2}
res = max(real_probs, key=real_probs.get)
odd_check = odd1 if res == "1" else oddX if res == "X" else odd2
conf = int(real_probs[res] * 100)

base = res

# Double Chance Analysis για κύρια πρόταση
dc_recommendations = analyze_double_chance(p1, pX, p2, odd1, oddX, odd2, h_t, a_t, st.session_state)

# Αν υπάρχει καλή πρόταση double chance, επηρέασε την κύρια πρόταση
if dc_recommendations:
    best_dc = max(dc_recommendations, key=lambda x: x['value'])
    if best_dc['value'] > 8 and best_dc['prob'] > 75 and best_dc['odds'] >= 1.40:
        base = best_dc['pick']

proposal = f"{base} (VALUE)"
st.session_state.current_proposal = proposal
color = "#2ecc71" if conf >= 65 else "#f1c40f" if conf >= 45 else "#e74c3c"

warning = ""
if total > 0 and (p1 + p2) < 0.40:
    warning = "⚠️ HIGH RISK MATCH: Statistics are very low, abstention is recommended."
elif odd1 <= 1.55 and pX > 0.28:
    warning = "⚠️ ΠΑΓΙΔΑ ΣΤΟ Χ: Το φαβορί δυσκολεύεται στα στατιστικά."

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

if warning:
    st.markdown(f'<div class="warning-box">{warning}</div>', unsafe_allow_html=True)

# ==============================
# DOUBLE CHANCE ANALYSIS SECTION
# ==============================
with st.expander("🛡️ Double Chance Analysis", expanded=False):
    
    # Ανάλυση double chance
    dc_recommendations = analyze_double_chance(p1, pX, p2, odd1, oddX, odd2, h_t, a_t, st.session_state)
    dc_reasons = get_double_chance_reason(p1, pX, p2, h_t, a_t, st.session_state)
    
    if dc_recommendations:
        st.markdown("### 🎯 Double Chance Opportunities")
        
        for rec in dc_recommendations:
            # Χρωματισμός με βάση απόδοση
            if rec['odds'] >= 1.80:
                bg_color = "#e8f5e9"
                border_color = "#2ecc71"
            elif rec['odds'] >= 1.50:
                bg_color = "#fff3e0"
                border_color = "#f39c12"
            else:
                bg_color = "#e3f2fd"
                border_color = "#3498db"
            
            # Value text
            if rec['value'] > 10:
                value_text = f"🔥 +{rec['value']:.1f}%"
                value_color = "#2ecc71"
            elif rec['value'] > 5:
                value_text = f"📈 +{rec['value']:.1f}%"
                value_color = "#f1c40f"
            else:
                value_text = f"⚖️ +{rec['value']:.1f}%"
                value_color = "#95a5a6"
            
            # Risk label
            risk_label = "🔴 Υψηλό" if rec['risk'] == 'high' else "🟡 Μέτριο" if rec['risk'] == 'medium' else "🟢 Χαμηλό"
            
            st.markdown(f"""
            <div class="dc-card" style="background-color: {bg_color}; border-left-color: {border_color};">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <span style="font-size: 2rem; font-weight: bold; color: #1e3c72;">{rec['pick']}</span>
                        <span style="font-size: 1.2rem; margin-left: 10px; background-color: white; padding: 3px 10px; border-radius: 15px;">
                            {rec['prob']:.1f}%
                        </span>
                    </div>
                    <div style="text-align: right;">
                        <div style="font-size: 1.8rem; font-weight: bold;">{rec['odds']:.2f}</div>
                        <div style="color: {value_color};">{value_text}</div>
                    </div>
                </div>
                <div style="margin-top: 10px; color: #34495e;">
                    📌 {rec['reason']}
                </div>
                <div style="margin-top: 5px; font-size: 0.9rem;">
                    Ρίσκο: {risk_label}
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("ℹ️ Δεν εντοπίστηκαν ευκαιρίες double chance με καλή απόδοση/πιθανότητα")
    
    # Στατιστικοί λόγοι
    if dc_reasons:
        with st.expander("📊 Στατιστικά Στοιχεία", expanded=False):
            for reason in dc_reasons:
                st.markdown(f"- {reason}")
    
    # Quick tips
    st.markdown("---")
    st.markdown("""
    **💡 Double Chance Tips:**
    - 🟢 **Χαμηλό ρίσκο**: Αποδόσεις 1.30-1.50, >75% πιθανότητα
    - 🟡 **Μέτριο ρίσκο**: Αποδόσεις 1.50-1.80, >70% πιθανότητα
    - 🔴 **Υψηλό ρίσκο**: Αποδόσεις 1.80+, >65% πιθανότητα + value
    """)

# ==============================
# ANALYTICAL EXPLANATIONS
# ==============================
with st.expander("🔍 Αναλυτική Εξήγηση Πρόβλεψης", expanded=False):
    
    explanations = generate_explanation(p1, pX, p2, odd1, oddX, odd2, h_t, a_t, st.session_state)
    metrics = calculate_key_metrics(p1, pX, p2, odd1, oddX, odd2)
    
    # Explanations σε δύο στήλες
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📋 Παράγοντες Πρόβλεψης")
        if explanations:
            for exp in explanations[:3]:
                st.markdown(f"- {exp}")
        else:
            st.markdown("- Ανεπαρκή στατιστικά για αναλυτική εξήγηση")
    
    with col2:
        st.markdown("### ⚖️ Ανάλυση Value")
        if len(explanations) > 3:
            for exp in explanations[3:]:
                st.markdown(f"- {exp}")
        else:
            value_map = {
                'home_edge': 'Άσος (1)',
                'draw_edge': 'Ισοπαλία (Χ)',
                'away_edge': 'Διπλό (2)'
            }
            
            value_amount = metrics.get('value_amount', 0)
            best_value = metrics.get('best_value', 'home_edge')
            
            if abs(value_amount) > 5:
                if value_amount > 0:
                    st.markdown(f"✅ **Value detected**: +{value_amount:.1f}% στο {value_map[best_value]}")
                else:
                    st.markdown(f"❌ **Overpriced**: {value_amount:.1f}% στο {value_map[best_value]}")
            else:
                st.markdown(f"⚖️ **Fair value**: {value_amount:.1f}% διαφορά")
    
    # Πίνακας σύγκρισης
    st.markdown("---")
    st.markdown("### 📈 Αναλυτική Σύγκριση Πιθανοτήτων")
    
    comp_data = {
        'Σημείο': ['1', 'X', '2'],
        'Απόδοση': [f"{odd1:.2f}", f"{oddX:.2f}", f"{odd2:.2f}"],
        'Μοντέλο': [f"{p1*100:.1f}%", f"{pX*100:.1f}%", f"{p2*100:.1f}%"],
        'Bookie': [f"{1/odd1*100:.1f}%", f"{1/oddX*100:.1f}%", f"{1/odd2*100:.1f}%"],
        'Διαφορά': [f"{p1*100 - 1/odd1*100:+.1f}%", 
                   f"{pX*100 - 1/oddX*100:+.1f}%", 
                   f"{p2*100 - 1/odd2*100:+.1f}%"]
    }
    
    st.dataframe(comp_data, use_container_width=True, hide_index=True)
    
    # Risk advice
    st.markdown("---")
    st.markdown("### 💡 Συμβουλή Διαχείρισης Ρίσκου")
    st.info(get_risk_advice(p1, pX, p2, conf))

st.markdown("---")

# ==============================
# INPUT FIELDS
# ==============================
c1, c2 = st.columns(2)
with c1:
    st.subheader("🏠 Γηπεδούχος")
    st.number_input("Νίκες", 0, 100, key="hw", help="Νίκες στα τελευταία 5 εντός έδρας")
    st.number_input("Ισοπαλίες", 0, 100, key="hd", help="Ισοπαλίες στα τελευταία 5 εντός έδρας")
    st.number_input("Ήττες", 0, 100, key="hl", help="Ήττες στα τελευταία 5 εντός έδρας")
with c2:
    st.subheader("🚀 Φιλοξενούμενος")
    st.number_input("Νίκες", 0, 100, key="aw", help="Νίκες στα τελευταία 5 εκτός έδρας")
    st.number_input("Ισοπαλίες", 0, 100, key="ad", help="Ισοπαλίες στα τελευταία 5 εκτός έδρας")
    st.number_input("Ήττες", 0, 100, key="al", help="Ήττες στα τελευταία 5 εκτός έδρας")

# ==============================
# MAIN BAR CHART
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

# Footer
st.markdown("---")
st.caption("BetAnalyzer v17.2.8 - Double Chance Analysis με έλεγχο απόδοσης")
