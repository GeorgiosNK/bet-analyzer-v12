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
.safety-badge {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 15px;
    border-radius: 10px;
    margin-top: 15px;
    text-align: left;
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
def analyze_double_chance(p1, pX, p2, odd1, oddX, odd2, h_t, a_t):
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
        home_losses = st.session_state.hl / h_t
        home_draws = st.session_state.hd / h_t
    else:
        home_losses = home_draws = 0.5
    
    if a_t > 0:
        away_losses = st.session_state.al / a_t
        away_draws = st.session_state.ad / a_t
    else:
        away_losses = away_draws = 0.5
    
    # ΕΙΔΙΚΟΣ ΚΑΝΟΝΑΣ ΓΙΑ 12
    if implied_12 > 0 and prob_12 > 0.80 and pX < 0.20:
        value = prob_12 - (1/implied_12)
        if value > 0.02:
            recommendations.append({
                'pick': '12',
                'prob': prob_12 * 100,
                'odds': implied_12,
                'value': value * 100,
                'risk': 'low',
                'reason': f"Σχεδόν σίγουρο όχι ισοπαλία - μόνο {pX*100:.1f}%"
            })
    
    # 1. Έλεγχος για 1X
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
    
    # 2. Έλεγχος για X2
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
    
    return recommendations

def get_double_chance_reason(p1, pX, p2, h_t, a_t):
    """
    Επιστρέφει στατιστικούς λόγους για double chance
    """
    reasons = []
    
    if h_t > 0:
        home_losses = st.session_state.hl / h_t
        home_draws = st.session_state.hd / h_t
        if home_losses < 0.15:
            reasons.append(f"🏠 Γηπεδούχος: Μόνο {home_losses*100:.0f}% ήττες εντός έδρας")
        if home_draws > 0.35:
            reasons.append(f"🤝 Γηπεδούχος: {home_draws*100:.0f}% ισοπαλίες")
    
    if a_t > 0:
        away_losses = st.session_state.al / a_t
        away_draws = st.session_state.ad / a_t
        if away_losses < 0.15:
            reasons.append(f"🚀 Φιλοξενούμενος: ΜΟΝΟ {away_losses*100:.1f}% ήττες εκτός έδρας!")
        if away_draws > 0.40:
            reasons.append(f"🤝 Φιλοξενούμενος: {away_draws*100:.1f}% ισοπαλίες εκτός έδρας!")
        if away_draws < 0.10 and a_t >= 10:
            reasons.append(f"⚡ Φιλοξενούμενος: ΜΟΝΟ {away_draws*100:.1f}% ισοπαλίες εκτός έδρας!")
    
    return reasons

# ==============================
# FUNCTIONS FOR EXPLANATIONS
# ==============================
def generate_explanation(p1, pX, p2, odd1, oddX, odd2, h_t, a_t):
    """
    Δημιουργεί αναλυτική εξήγηση για την πρόταση
    """
    explanation_parts = []
    
    # Υπολογισμός πραγματικής ισοπαλίας από στατιστικά
    if h_t > 0 and a_t > 0:
        real_draw_pct = (st.session_state.hd + st.session_state.ad) / (h_t + a_t)
        
        if real_draw_pct < 0.15:
            explanation_parts.append(f"⚡ **ΠΟΛΥ ΧΑΜΗΛΟ Χ ΣΤΑ ΣΤΑΤΙΣΤΙΚΑ**: {real_draw_pct*100:.1f}% - Ιδανικό για 12")
        elif real_draw_pct < 0.20:
            explanation_parts.append(f"⚡ **Χαμηλό Χ στα στατιστικά**: {real_draw_pct*100:.1f}% - Σκέψου 12")
    
    # Ειδικός έλεγχος για φιλοξενούμενο με πολύ λίγες ήττες
    if a_t >= 10 and st.session_state.al / a_t < 0.15:
        explanation_parts.append(f"🛡️ **ΦΙΛΟΞΕΝΟΥΜΕΝΟΣ**: Μόνο {(st.session_state.al / a_t)*100:.1f}% ήττες εκτός έδρας - ΔΥΣΚΟΛΑ ΧΑΝΕΙ!")
    
    # Ειδικός έλεγχος για φιλοξενούμενο με πολλές ισοπαλίες
    if a_t >= 10 and st.session_state.ad / a_t > 0.40:
        explanation_parts.append(f"🤝 **ΦΙΛΟΞΕΝΟΥΜΕΝΟΣ**: {(st.session_state.ad / a_t)*100:.1f}% ισοπαλίες εκτός έδρας - Το Χ έχει αξία!")
    
    # 1. Ανάλυση στατιστικών
    if h_t > 0 and a_t > 0:
        h_pos = (st.session_state.hw + st.session_state.hd) / h_t
        a_pos = (st.session_state.aw + st.session_state.ad) / a_t
        
        if h_pos > 0.7:
            explanation_parts.append("🏠 **Ισχυρή εντός έδρας ομάδα**: Η γηπεδούχος έχει πολύ καλή φόρμα")
        elif a_pos > 0.7:
            explanation_parts.append("🚀 **Ισχυρή εκτός έδρας ομάδα**: Η φιλοξενούμενη έχει πολύ καλή φόρμα")
        
        if h_t > 0 and st.session_state.hw > st.session_state.hl * 2:
            explanation_parts.append("⚽ **Επιθετικό πλεονέκτημα**: Η γηπεδούχος σκοράρει συχνά")
        
        if a_t > 0 and st.session_state.aw > st.session_state.al * 2:
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
    
    # 3. Ανάλυση Χ (ισοπαλίας) - Σύγκριση με στατιστικά
    if oddX > 1.01 and h_t > 0 and a_t > 0:
        real_draw_pct = (st.session_state.hd + st.session_state.ad) / (h_t + a_t)
        implied_draw = 1/oddX * 100
        
        if real_draw_pct < 0.15 and implied_draw > 25:
            explanation_parts.append(f"⚠️ **ΠΑΓΙΔΑ ΣΤΟ Χ**: Η απόδοση {oddX:.2f} είναι πολύ μικρή για {real_draw_pct*100:.1f}% πραγματική πιθανότητα")
    
    # 4. Εξήγηση τελικής πρότασης
    proposal = st.session_state.get('current_proposal', '')
    
    if "1X" in proposal:
        explanation_parts.append("🛡️ **Κάλυψη**: Προτείνεται διπλή ευκαιρία 1X λόγω στατιστικών")
    elif "X2" in proposal:
        explanation_parts.append("🛡️ **Κάλυψη**: Προτείνεται διπλή ευκαιρία X2 λόγω στατιστικών")
    elif "12" in proposal:
        explanation_parts.append("🎯 **ΚΑΘΟΛΟΥ ΙΣΟΠΑΛΙΑ**: Προτείνεται 12 λόγω πολύ χαμηλού ποσοστού Χ στα στατιστικά")
    
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

def get_risk_advice(p1, pX, p2, conf, total):
    """
    Επιστρέφει συμβουλές διαχείρισης ρίσκου
    """
    if total < 8:
        return "🔴 **ΑΝΕΠΑΡΚΗ ΔΕΔΟΜΕΝΑ**: Λιγότερα από 8 συνολικά παιχνίδια - Αποφυγή"
    elif conf >= 70:
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
# CALCULATIONS ENGINE
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

# ΒΕΛΤΙΩΣΗ: Μείωσε το max alpha στο 0.7 (70% βάρος στα stats, 30% στις αποδόσεις)
max_alpha = 0.7
alpha = min(max_alpha, total / 20) if total > 0 else 0

# ΒΕΛΤΙΩΣΗ: Πιο ήπιο loss penalty (0.4)
loss_penalty = 0.4

# Υπολογισμός win ratios
h_wr = (st.session_state.hw - (st.session_state.hl * loss_penalty)) / h_t if h_t > 0 else pm1
a_wr = (st.session_state.aw - (st.session_state.al * loss_penalty)) / a_t if a_t > 0 else pm2

# Υπολογισμός points
home_points = st.session_state.hw * 3 + st.session_state.hd
away_points = st.session_state.aw * 3 + st.session_state.ad

# Μπόνους για καλύτερη ομάδα (πιο ήπιο)
if h_t >= 10 and a_t >= 10:
    if home_points > away_points * 1.2:
        h_wr = h_wr * 1.1
        a_wr = a_wr * 0.95
    elif away_points > home_points * 1.2:
        a_wr = a_wr * 1.1
        h_wr = h_wr * 0.95

# Υπολογισμός πιθανοτήτων
p1 = alpha * h_wr + (1-alpha) * pm1
p2 = alpha * a_wr + (1-alpha) * pm2

p1, p2 = max(0.10, p1), max(0.10, p2)
pX = max(0.01, 1 - p1 - p2)

# ==============================
# ΔΙΟΡΘΩΣΗ #1: ΜΗΝ ΑΓΝΟΕΙΣ ΤΙΣ ΙΣΟΠΑΛΙΕΣ ΤΗΣ ΓΗΠΕΔΟΥΧΟΥ (ΑΜΕΣΩΣ ΜΕΤΑ!)
# ==============================
if h_t > 0 and a_t > 0:
    home_draw_pct = st.session_state.hd / h_t
    away_draw_pct = st.session_state.ad / a_t
    
    # Αν η φιλοξενούμενη έχει 0% ισοπαλίες αλλά η γηπεδούχος έχει >15%
    if away_draw_pct < 0.05 and home_draw_pct > 0.15:
        # Το Χ δεν μπορεί να είναι μικρότερο από το 40% των ισοπαλιών της γηπεδούχου
        min_allowable_pX = home_draw_pct * 0.4
        
        if pX < min_allowable_pX:
            old_pX = pX
            pX = min_allowable_pX
            # Ανακατανομή - κράτα την ίδια αναλογία p1/p2
            remaining = 1 - pX
            if remaining > 0 and (p1 + p2) > 0:
                p1 = p1 / (p1 + p2) * remaining
                p2 = p2 / (p1 + p2) * remaining
            
            st.session_state.draw_correction = True
            warning = "⚠️ Η γηπεδούχος έχει ισοπαλίες - Μην αγνοείτε το Χ"

# ==============================
# ΠΡΑΓΜΑΤΙΚΗ ΙΣΟΠΑΛΙΑ ΑΠΟ ΣΤΑΤΙΣΤΙΚΑ (ΜΕΤΑ τη διόρθωση)
# ==============================
if h_t > 0 and a_t > 0 and total >= 8:
    real_draw_pct = (st.session_state.hd + st.session_state.ad) / (h_t + a_t)
    away_draw_pct = st.session_state.ad / a_t if a_t > 0 else 0.25
    away_loss_pct = st.session_state.al / a_t if a_t > 0 else 0.25
    
    # ΕΙΔΙΚΟΣ ΚΑΝΟΝΑΣ 1: Φιλοξενούμενος με πολύ λίγες ήττες (<15%)
    if away_loss_pct < 0.15 and a_t >= 8:
        p2 = p2 * 0.6
        remaining = 1 - p2
        if remaining > 0 and (p1 + pX) > 0:
            p1 = p1 / (p1 + pX) * remaining
            pX = pX / (p1 + pX) * remaining
        st.session_state.away_special = "low_losses"
        if 'warning' not in locals():
            warning = "⚠️ ΦΙΛΟΞΕΝΟΥΜΕΝΟΣ ΜΕ ΕΛΑΧΙΣΤΕΣ ΗΤΤΕΣ ΕΚΤΟΣ - Δύσκολα χάνει!"
    
    # ΕΙΔΙΚΟΣ ΚΑΝΟΝΑΣ 2: Φιλοξενούμενος με πολλές ισοπαλίες (>40%)
    if away_draw_pct > 0.40 and a_t >= 8:
        pX = pX * 1.15
        total_prob = p1 + pX + p2
        if total_prob > 0:
            p1 = p1 / total_prob
            pX = pX / total_prob
            p2 = p2 / total_prob
        st.session_state.away_special = "high_draws"
        if 'warning' not in locals():
            warning = "⚠️ ΦΙΛΟΞΕΝΟΥΜΕΝΟΣ ΜΕ ΠΟΛΛΕΣ ΙΣΟΠΑΛΙΕΣ ΕΚΤΟΣ - Το Χ έχει αξία!"

real_h_draw = st.session_state.hd / h_t if h_t > 0 else 0.25
real_a_draw = st.session_state.ad / a_t if a_t > 0 else 0.25
avg_draw = (real_h_draw + real_a_draw) / 2

# Draw Normalization (πιο ήπια)
if pX > 0.45 and avg_draw < 0.30:
    diff = pX - 0.45
    p1 += diff * 0.4
    p2 += diff * 0.4
    pX = 0.45

s = p1 + pX + p2
if s > 0:
    p1, pX, p2 = p1/s, pX/s, p2/s

# ==============================
# FINAL LOGIC ENGINE
# ==============================
real_probs = {'1': p1, 'X': pX, '2': p2}
res = max(real_probs, key=real_probs.get)
odd_check = odd1 if res == "1" else oddX if res == "X" else odd2
base_conf = int(real_probs[res] * 100)

base = res

# ==============================
# ΥΠΟΛΟΓΙΣΜΟΣ ΔΙΠΛΗΣ ΕΥΚΑΙΡΙΑΣ ΓΙΑ ΚΥΡΙΟ ΑΠΟΤΕΛΕΣΜΑ
# ==============================
prob_1X = p1 + pX
prob_X2 = pX + p2
prob_12 = p1 + p2

implied_1X = 1 / (1/odd1 + 1/oddX) if odd1 > 1.0 and oddX > 1.0 else 0
implied_X2 = 1 / (1/oddX + 1/odd2) if oddX > 1.0 and odd2 > 1.0 else 0
implied_12 = 1 / (1/odd1 + 1/odd2) if odd1 > 1.0 and odd2 > 1.0 else 0

double_chance_suggestion = ""
double_chance_odds = 0
double_chance_prob = 0

# Μόνο αν το base είναι καθαρό σημείο (1, X, 2)
if base in ["1", "X", "2"]:
    # Αν το κύριο σημείο είναι 1
    if base == "1":
        if prob_1X > 0.70 and implied_1X > 1.30:
            double_chance_suggestion = "1X"
            double_chance_odds = implied_1X
            double_chance_prob = prob_1X * 100
        elif prob_12 > 0.80 and implied_12 > 1.25:
            double_chance_suggestion = "12"
            double_chance_odds = implied_12
            double_chance_prob = prob_12 * 100

    # Αν το κύριο σημείο είναι 2
    elif base == "2":
        if prob_X2 > 0.70 and implied_X2 > 1.30:
            double_chance_suggestion = "X2"
            double_chance_odds = implied_X2
            double_chance_prob = prob_X2 * 100
        elif prob_12 > 0.80 and implied_12 > 1.25:
            double_chance_suggestion = "12"
            double_chance_odds = implied_12
            double_chance_prob = prob_12 * 100

    # Αν το κύριο σημείο είναι Χ
    elif base == "X":
        if prob_1X > 0.70 and implied_1X > 1.30:
            double_chance_suggestion = "1X"
            double_chance_odds = implied_1X
            double_chance_prob = prob_1X * 100
        elif prob_X2 > 0.70 and implied_X2 > 1.30:
            double_chance_suggestion = "X2"
            double_chance_odds = implied_X2
            double_chance_prob = prob_X2 * 100

# ==============================
# CONFIDENCE & PROPOSAL FINALIZATION
# ==============================

# Αρχικοποίηση μεταβλητών
proposal = ""
conf = 0
color = "#95a5a6"

# Έλεγχος στατιστικής επάρκειας
if total < 6:
    proposal = "🚫 NO BET"
    warning = "⚠️ ΑΝΕΠΑΡΚΗ ΣΤΑΤΙΣΤΙΚΑ: Χρειάζονται τουλάχιστον 6 συνολικά παιχνίδια"
    conf = 0
    color = "#95a5a6"
else:
    # ΕΙΔΙΚΟΣ ΚΑΝΟΝΑΣ ΓΙΑ 12
    if h_t > 0 and a_t > 0:
        real_draw_pct = (st.session_state.hd + st.session_state.ad) / (h_t + a_t)
        away_draw_pct = st.session_state.ad / a_t if a_t > 0 else 0.25
        
        if (real_draw_pct < 0.15 or away_draw_pct < 0.10) and total >= 10:
            # Πριν προτείνεις 12, έλεγξε αν η γηπεδούχος έχει ισοπαλίες
            home_draw_pct = st.session_state.hd / h_t if h_t > 0 else 0
            if home_draw_pct < 0.15:  # Μόνο αν και η γηπεδούχος έχει λίγες ισοπαλίες
                base = "12"
                base_conf = int(prob_12 * 100)
                warning = "✅ ΠΡΟΤΕΙΝΕΤΑΙ 12: Ελάχιστες ισοπαλίες στα στατιστικά"
    
    # Κανονικός υπολογισμός confidence - ΜΕ ΕΛΕΓΧΟ ΓΙΑ ΤΟ base
    if base in real_probs:
        base_conf = int(real_probs[base] * 100)
    else:
        # Αν το base είναι "12", "1X", "X2", υπολόγισε από τα επιμέρους
        if base == "12":
            base_conf = int((p1 + p2) * 100)
        elif base == "1X":
            base_conf = int((p1 + pX) * 100)
        elif base == "X2":
            base_conf = int((pX + p2) * 100)
        else:
            base_conf = 50
    
    if total < 10:
        confidence_multiplier = total / 10
        conf = int(base_conf * confidence_multiplier)
        conf = min(conf, 60)
        if not warning and total < 8:
            warning = "⚠️ ΜΕΙΩΜΕΝΗ ΑΞΙΟΠΙΣΤΙΑ: Λίγα στατιστικά δεδομένα"
    elif total < 15:
        conf = min(base_conf, 70)
    else:
        conf = min(base_conf, 85)
    
    # ΣΗΜΑΝΤΙΚΟ: Το confidence δεν μπορεί να ξεπερνά την πραγματική πιθανότητα
    if base in real_probs:
        actual_prob = int(real_probs[base] * 100)
    else:
        if base == "12":
            actual_prob = int((p1 + p2) * 100)
        elif base == "1X":
            actual_prob = int((p1 + pX) * 100)
        elif base == "X2":
            actual_prob = int((pX + p2) * 100)
        else:
            actual_prob = conf
    
    conf = min(conf, actual_prob)
    
    # Επιπλέον έλεγχοι μόνο αν δεν έχει ήδη οριστεί ως 12 και είναι καθαρό σημείο
    if base != "12" and base in real_probs:
        if pX < 0.25 and res == "X":
            if p1 > p2:
                base = "1X"
            else:
                base = "X2"
            conf = min(conf, 45)
        
        if h_t >= 5 and st.session_state.hw == 0 and a_t >= 5 and st.session_state.al >= 3:
            base = "X2"
            conf = min(conf, 50)
    
    # Double Chance Analysis (μόνο για καθαρά σημεία)
    dc_recommendations = analyze_double_chance(p1, pX, p2, odd1, oddX, odd2, h_t, a_t)
    
    if dc_recommendations and total >= 10 and base != "12" and base in real_probs:
        best_dc = max(dc_recommendations, key=lambda x: x['value'])
        if best_dc['value'] > 8 and best_dc['prob'] > 75 and best_dc['odds'] >= 1.40:
            base = best_dc['pick']
    
    # Τελικό proposal
    proposal = f"{base} (VALUE)"
    
    # Χρώμα confidence
    if conf >= 65:
        color = "#2ecc71"
    elif conf >= 45:
        color = "#f1c40f"
    else:
        color = "#e74c3c"

st.session_state.current_proposal = proposal

# ==============================
# UI OUTPUT
# ==============================
# ΕΜΦΑΝΙΣΗ ΕΝΑΛΛΑΚΤΙΚΗΣ ΜΟΝΟ ΑΝ ΕΙΝΑΙ ΠΑΝΩ ΑΠΟ 70% ΚΑΙ ΔΕΝ ΕΙΝΑΙ ΤΟ ΙΔΙΟ ΜΕ ΤΟ ΚΥΡΙΟ
if (double_chance_suggestion and 
    double_chance_prob >= 70 and 
    double_chance_suggestion != base and
    total >= 8):
    
    st.markdown(f"""
    <div class="result-card">
        <div style="color:gray;font-weight:bold;margin-bottom:5px;">📊 BetAnalyzer v17.2.8</div>
        <div style="font-size:3.5rem;font-weight:900;color:#1e3c72;line-height:1;">{proposal}</div>
        <div style="font-size:1.8rem;font-weight:bold;color:{color};margin-top:10px;">{conf}% Confidence</div>
        <div class="safety-badge">
            <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap;">
                <div>
                    <span style="font-size:1.1rem; opacity:0.9;">🛡️ Εναλλακτική ασφαλείας</span><br>
                    <span style="font-size:2.2rem; font-weight:bold;">{double_chance_suggestion}</span>
                </div>
                <div style="text-align:right;">
                    <span style="font-size:1.5rem; font-weight:bold;">{double_chance_odds:.2f}</span><br>
                    <span style="font-size:1.1rem;">{double_chance_prob:.1f}% πιθανότητα</span>
                </div>
            </div>
            <div style="margin-top:10px; font-size:0.9rem; opacity:0.9;">
                💡 Αν θέλεις μεγαλύτερη ασφάλεια, η διπλή ευκαιρία {double_chance_suggestion} έχει υψηλή πιθανότητα!
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
else:
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
    
    dc_recommendations = analyze_double_chance(p1, pX, p2, odd1, oddX, odd2, h_t, a_t)
    dc_reasons = get_double_chance_reason(p1, pX, p2, h_t, a_t)
    
    # Φιλτράρισμα για να μην εμφανίζεται η ίδια επιλογή με την κύρια πρόταση
    filtered_dc = [rec for rec in dc_recommendations if rec['pick'] != base]
    
    if filtered_dc and total >= 6:
        st.markdown("### 🎯 Double Chance Opportunities")
        
        for rec in filtered_dc:
            if rec['odds'] >= 1.80:
                bg_color = "#e8f5e9"
                border_color = "#2ecc71"
            elif rec['odds'] >= 1.50:
                bg_color = "#fff3e0"
                border_color = "#f39c12"
            else:
                bg_color = "#e3f2fd"
                border_color = "#3498db"
            
            if rec['value'] > 10:
                value_text = f"🔥 +{rec['value']:.1f}%"
                value_color = "#2ecc71"
            elif rec['value'] > 5:
                value_text = f"📈 +{rec['value']:.1f}%"
                value_color = "#f1c40f"
            else:
                value_text = f"⚖️ +{rec['value']:.1f}%"
                value_color = "#95a5a6"
            
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
        if total < 6:
            st.info("ℹ️ Ανεπαρκή δεδομένα για ανάλυση double chance")
        else:
            st.info("ℹ️ Δεν εντοπίστηκαν ευκαιρίες double chance με καλή απόδοση/πιθανότητα")
    
    if dc_reasons and total >= 6:
        with st.expander("📊 Στατιστικά Στοιχεία", expanded=False):
            for reason in dc_reasons:
                st.markdown(f"- {reason}")
    
    if h_t > 0 and a_t > 0 and total >= 6:
        real_draw_pct = (st.session_state.hd + st.session_state.ad) / (h_t + a_t)
        away_draw_pct = st.session_state.ad / a_t if a_t > 0 else 0
        away_loss_pct = st.session_state.al / a_t if a_t > 0 else 0
        home_draw_pct = st.session_state.hd / h_t if h_t > 0 else 0
        st.markdown(f"**📊 Πραγματικό ποσοστό ισοπαλίας:** {real_draw_pct*100:.1f}%")
        st.markdown(f"**📊 Γηπεδούχος ισοπαλίες εντός:** {home_draw_pct*100:.1f}%")
        st.markdown(f"**📊 Φιλοξενούμενος ισοπαλίες εκτός:** {away_draw_pct*100:.1f}%")
        st.markdown(f"**📊 Φιλοξενούμενος ήττες εκτός:** {away_loss_pct*100:.1f}%")
    
    st.markdown("---")
    st.markdown("""
    **💡 Double Chance Tips:**
    - 🟢 **Χαμηλό ρίσκο**: Αποδόσεις 1.30-1.50, >75% πιθανότητα
    - 🟡 **Μέτριο ρίσκο**: Αποδόσεις 1.50-1.80, >70% πιθανότητα
    - 🔴 **Υψηλό ρίσκο**: Αποδόσεις 1.80+, >65% πιθανότητα + value
    - ⚡ **12 (όχι ισοπαλία)**: Όταν η πραγματική ισοπαλία στα στατιστικά είναι <15%
    """)

# ==============================
# ANALYTICAL EXPLANATIONS
# ==============================
with st.expander("🔍 Αναλυτική Εξήγηση Πρόβλεψης", expanded=False):
    
    if total >= 6:
        explanations = generate_explanation(p1, pX, p2, odd1, oddX, odd2, h_t, a_t)
        metrics = calculate_key_metrics(p1, pX, p2, odd1, oddX, odd2)
        
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
        
        prob_12 = p1 + p2
        implied_12 = 1 / (1/odd1 + 1/odd2)
        comp_data['Σημείο'].append('12')
        comp_data['Απόδοση'].append(f"{implied_12:.2f}")
        comp_data['Μοντέλο'].append(f"{prob_12*100:.1f}%")
        comp_data['Bookie'].append(f"{1/implied_12*100:.1f}%")
        comp_data['Διαφορά'].append(f"{prob_12*100 - 1/implied_12*100:+.1f}%")
        
        st.dataframe(comp_data, use_container_width=True, hide_index=True)
        
        st.markdown("---")
        st.markdown("### 💡 Συμβουλή Διαχείρισης Ρίσκου")
        st.info(get_risk_advice(p1, pX, p2, conf, total))
    else:
        st.info("ℹ️ Ανεπαρκή δεδομένα για αναλυτική εξήγηση (χρειάζονται ≥6 συνολικά παιχνίδια)")

st.markdown("---")

# ==============================
# INPUT FIELDS
# ==============================
c1, c2 = st.columns(2)
with c1:
    st.subheader("🏠 Γηπεδούχος")
    st.number_input("Νίκες", 0, 100, key="hw", help="Νίκες σε όλους τους εντός έδρας αγώνες")
    st.number_input("Ισοπαλίες", 0, 100, key="hd", help="Ισοπαλίες σε όλους τους εντός έδρας αγώνες")
    st.number_input("Ήττες", 0, 100, key="hl", help="Ήττες σε όλους τους εντός έδρας αγώνες")
with c2:
    st.subheader("🚀 Φιλοξενούμενος")
    st.number_input("Νίκες", 0, 100, key="aw", help="Νίκες σε όλους τους εκτός έδρας αγώνες")
    st.number_input("Ισοπαλίες", 0, 100, key="ad", help="Ισοπαλίες σε όλους τους εκτός έδρας αγώνες")
    st.number_input("Ήττες", 0, 100, key="al", help="Ήττες σε όλους τους εκτός έδρας αγώνες")

# ==============================
# MAIN BAR CHART
# ==============================
if total >= 6:
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
else:
    st.info("📊 Συμπληρώστε τουλάχιστον 6 συνολικά παιχνίδια για να εμφανιστεί το γράφημα")

# Footer
st.markdown("---")
st.caption("BetAnalyzer v17.2.8 - Double Chance Analysis με έλεγχο απόδοσης και διόρθωση ισοπαλιών")
