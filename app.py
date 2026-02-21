import streamlit as st
import plotly.graph_objects as go
import streamlit.components.v1 as components

# ==============================
# CONFIG
# ==============================
st.set_page_config(page_title="BetAnalyzer v17.3.8", page_icon="⚽", layout="centered")

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
.main-proposal {
    font-size: 3.5rem;
    font-weight: 900;
    color: #1e3c72;
    line-height: 1.2;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-wrap: wrap;
    gap: 10px;
}
.main-number {
    font-size: 3.5rem;
    font-weight: 900;
    color: #1e3c72;
    line-height: 1.2;
}
.double-chance {
    font-size: 2.8rem;
    font-weight: 900;
    color: #1e3c72;
    line-height: 1.2;
}
.double-percent {
    font-size: 1.6rem;
    font-weight: 600;
    margin-left: 5px;
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
        if away_losses < 0.20:
            reasons.append(f"🚀 Φιλοξενούμενος: Μόνο {away_losses*100:.0f}% ήττες εκτός έδρας")
        if away_draws > 0.35:
            reasons.append(f"🤝 Φιλοξενούμενος: {away_draws*100:.0f}% ισοπαλίες")
        if away_draws < 0.10 and a_t >= 10:
            reasons.append(f"⚡ Φιλοξενούμενος: ΜΟΝΟ {away_draws*100:.1f}% ισοπαλίες εκτός έδρας!")
    
    return reasons

# ==============================
# FUNCTIONS FOR EXPLANATIONS
# ==============================
def generate_explanation(p1, pX, p2, odd1, oddX, odd2, h_t, a_t, main_point, top_two, sorted_stats):
    """
    Δημιουργεί αναλυτική εξήγηση για την πρόταση
    """
    explanation_parts = []
    
    # Υπολογισμός ποσοστού Χ από το μοντέλο
    if h_t > 0 and a_t > 0:
        model_draw_pct = pX * 100
        
        if model_draw_pct < 15:
            explanation_parts.append(f"⚡ **ΠΟΛΥ ΧΑΜΗΛΟ Χ ΣΤΟ ΜΟΝΤΕΛΟ**: {model_draw_pct:.1f}% - Η πρόταση {top_two} βασίζεται στα δύο επικρατέστερα αποτελέσματα")
        elif model_draw_pct < 20:
            explanation_parts.append(f"⚡ **Χαμηλό Χ στο μοντέλο**: {model_draw_pct:.1f}% - Η πρόταση {top_two} επιλέχθηκε ως κάλυψη")
    
    # Ειδικός έλεγχος για φιλοξενούμενο με πολύ λίγες ισοπαλίες
    if a_t >= 10 and st.session_state.ad / a_t < 0.10:
        explanation_parts.append(f"🚨 **ΦΙΛΟΞΕΝΟΥΜΕΝΟΣ**: Μόνο {(st.session_state.ad / a_t)*100:.1f}% ισοπαλίες εκτός έδρας!")
    
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
    
    # 3. Εξήγηση τελικής πρότασης
    proposal = st.session_state.get('current_proposal', '')
    
    if "1X" in proposal:
        explanation_parts.append(f"🛡️ **Κάλυψη**: Προτείνεται διπλή ευκαιρία 1X ως κάλυψη των δύο επικρατέστερων αποτελεσμάτων ({main_point} και Χ)")
    elif "X2" in proposal:
        explanation_parts.append(f"🛡️ **Κάλυψη**: Προτείνεται διπλή ευκαιρία X2 ως κάλυψη των δύο επικρατέστερων αποτελεσμάτων (Χ και 2)")
    elif "12" in proposal:
        explanation_parts.append(f"🎯 **ΚΑΘΟΛΟΥ ΙΣΟΠΑΛΙΑ**: Προτείνεται 12 ως κάλυψη των δύο επικρατέστερων αποτελεσμάτων (1 και 2)")
    
    if "1" in proposal and "VALUE" not in proposal:
        explanation_parts.append(f"✅ **Καθαρό φαβορί**: Το {main_point} επιλέχθηκε ως κύριο σημείο (μεγαλύτερο ποσοστό: {sorted_stats[0][1]*100:.1f}%)")
    elif "2" in proposal and "VALUE" not in proposal:
        explanation_parts.append(f"✅ **Καθαρό φαβορί**: Το {main_point} επιλέχθηκε ως κύριο σημείο (μεγαλύτερο ποσοστό: {sorted_stats[0][1]*100:.1f}%)")
    elif "X" in proposal and "VALUE" not in proposal:
        explanation_parts.append(f"⚠️ **Ισοπαλία**: Το {main_point} επιλέχθηκε ως κύριο σημείο (μεγαλύτερο ποσοστό: {sorted_stats[0][1]*100:.1f}%)")
    
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

def get_risk_advice(p1, pX, p2, conf, total, top_two_prob, main_point, top_two):
    """
    Επιστρέφει συμβουλές διαχείρισης ρίσκου
    """
    if total < 8:
        return "🔴 **ΑΝΕΠΑΡΚΗ ΔΕΔΟΜΕΝΑ**: Λιγότερα από 8 συνολικά παιχνίδια - Αποφυγή"
    
    # Αν η διπλή ευκαιρία έχει πολύ υψηλό ποσοστό
    if top_two_prob >= 80:
        return f"🟢 **ΠΟΛΥ ΥΨΗΛΗ ΠΙΘΑΝΟΤΗΤΑ ΚΑΛΥΨΗΣ**: Η διπλή ευκαιρία {top_two} έχει {top_two_prob:.1f}% - Ιδανικό για safe bet, ενώ το κύριο σημείο {main_point} έχει {conf}% confidence"
    elif top_two_prob >= 70:
        return f"🟡 **ΚΑΛΗ ΠΙΘΑΝΟΤΗΤΑ ΚΑΛΥΨΗΣ**: Η διπλή ευκαιρία {top_two} έχει {top_two_prob:.1f}% - Κατάλληλο για normal bet, το κύριο σημείο {main_point} έχει {conf}% confidence"
    
    # Αλλιώς βασιζόμαστε στο confidence του κυρίου σημείου
    if conf >= 70:
        return f"🟢 **Υψηλή εμπιστοσύνη στο κύριο σημείο**: Το {main_point} έχει {conf}% confidence - Κατάλληλο για κανονικό ποντάρισμα"
    elif conf >= 50:
        return f"🟡 **Μέτρια εμπιστοσύνη στο κύριο σημείο**: Το {main_point} έχει {conf}% confidence - Μείωση ποντάρισματος ή προτίμηση στη διπλή ευκαιρία {top_two} ({top_two_prob:.1f}%)"
    else:
        return f"🔴 **Χαμηλή εμπιστοσύνη στο κύριο σημείο**: Το {main_point} έχει μόνο {conf}% confidence - Μικρό ποντάρισμα ή αποφυγή"

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
# ΠΡΑΓΜΑΤΙΚΗ ΙΣΟΠΑΛΙΑ ΑΠΟ ΣΤΑΤΙΣΤΙΚΑ
# ==============================
if h_t > 0 and a_t > 0 and total >= 8:
    real_draw_pct = (st.session_state.hd + st.session_state.ad) / (h_t + a_t)
    away_draw_pct = st.session_state.ad / a_t if a_t > 0 else 0.25
    
    if real_draw_pct < 0.18 or away_draw_pct < 0.10:
        reduction = 0.35 if real_draw_pct < 0.15 else 0.20
        pX = pX * (1 - reduction)
        
        remaining = 1 - pX
        if remaining > 0:
            p1 = p1 / (p1 + p2) * remaining
            p2 = p2 / (p1 + p2) * remaining

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
# ΥΠΟΛΟΓΙΣΜΟΣ ΠΡΟΤΑΣΗΣ (v17.3.8)
# ==============================
# Δημιουργία λίστας με τα p1, pX, p2 από το μοντέλο
stats_list = [
    ("1", p1),
    ("X", pX),
    ("2", p2)
]

# Ταξινόμηση με βάση το ποσοστό (από μεγαλύτερο σε μικρότερο)
sorted_stats = sorted(stats_list, key=lambda x: x[1], reverse=True)

# Καθαρό σημείο = το μεγαλύτερο ποσοστό
main_point = sorted_stats[0][0]

# Διπλή ευκαιρία = τα δύο μεγαλύτερα ποσοστά
top_two = sorted_stats[0][0] + sorted_stats[1][0]
top_two_prob = (sorted_stats[0][1] + sorted_stats[1][1]) * 100

# Χρώμα για το ποσοστό της διπλής ευκαιρίας (ίδια λογική με το confidence)
if top_two_prob >= 65:
    dc_color = "#2ecc71"  # Πράσινο
elif top_two_prob >= 45:
    dc_color = "#f1c40f"  # Κίτρινο
else:
    dc_color = "#e74c3c"  # Κόκκινο

# ==============================
# CONFIDENCE & PROPOSAL FINALIZATION
# ==============================

# Αρχικοποίηση μεταβλητών
proposal = ""
warning = ""
conf = 0
color = "#95a5a6"

# Έλεγχος στατιστικής επάρκειας
if total < 6:
    proposal = "🚫 NO BET"
    warning = "⚠️ ΑΝΕΠΑΡΚΗ ΣΤΑΤΙΣΤΙΚΑ: Χρειάζονται τουλάχιστον 6 συνολικά παιχνίδια"
    conf = 0
    color = "#95a5a6"
    main_point = "🚫"
    top_two = ""
    top_two_prob = 0
else:
    # Υπολογισμός confidence (από το μεγαλύτερο ποσοστό)
    base_conf = int(sorted_stats[0][1] * 100)
    
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
    
    # Χρώμα confidence
    if conf >= 65:
        color = "#2ecc71"
    elif conf >= 45:
        color = "#f1c40f"
    else:
        color = "#e74c3c"
    
    # Προσθήκη στατιστικής παρατήρησης αν το Χ είναι πολύ χαμηλό
    real_draw_total = (st.session_state.hd + st.session_state.ad) / (h_t + a_t) if (h_t + a_t) > 0 else 0
    if real_draw_total < 0.15:
        warning = f"📊 ΣΤΑΤΙΣΤΙΚΗ ΠΑΡΑΤΗΡΗΣΗ: Η ισοπαλία εμφανίζεται μόνο {real_draw_total*100:.1f}% στα στατιστικά. Η πρόταση {top_two} βασίζεται στα δύο επικρατέστερα αποτελέσματα."

st.session_state.current_proposal = f"{main_point} ({top_two})"

# ==============================
# UI OUTPUT
# ==============================
if total >= 6:
    st.markdown(f"""
    <div class="result-card">
        <div style="color:gray;font-weight:bold;margin-bottom:5px;">📊 BetAnalyzer v17.3.8</div>
        <div class="main-proposal">
            <span class="main-number">{main_point}</span>
            <span class="double-chance">({top_two} <span class="double-percent" style="color: {dc_color};">{top_two_prob:.1f}%</span>)</span>
        </div>
        <div style="font-size:1.8rem;font-weight:bold;color:{color};margin-top:10px;">{conf}% Confidence</div>
        <div style="margin-top:15px; font-family: monospace; font-size: 1rem; color: #555;">
            [MODEL]: 1: {p1*100:.1f}% | X: {pX*100:.1f}% | 2: {p2*100:.1f}%
        </div>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown(f"""
    <div class="result-card">
        <div style="color:gray;font-weight:bold;margin-bottom:5px;">📊 BetAnalyzer v17.3.8</div>
        <div class="main-proposal">
            <span class="main-number">{main_point}</span>
        </div>
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
    
    # Πάντα να υπάρχει επεξήγηση για τη διπλή ευκαιρία που προτείνουμε
    if total >= 6:
        st.markdown(f"### 📊 Ανάλυση Πρότασης")
        st.markdown(f"""
        - **Κύριο σημείο:** {main_point} ({sorted_stats[0][1]*100:.1f}%)
        - **Διπλή ευκαιρία:** {top_two} ({top_two_prob:.1f}%)
        - **Επεξήγηση:** Επιλέχθηκε το {main_point} ως κύριο σημείο (μεγαλύτερο ποσοστό) και {top_two} ως κάλυψη (τα δύο μεγαλύτερα ποσοστά).
        """)
    
    # Υπόλοιπες ευκαιρίες double chance (αν υπάρχουν)
    if dc_recommendations and total >= 6:
        st.markdown("### 🎯 Άλλες Double Chance Opportunities")
        
        for rec in dc_recommendations:
            # Αν η πρόταση είναι διαφορετική από αυτή που ήδη δείξαμε
            if rec['pick'] != top_two:
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
            st.info("ℹ️ Δεν εντοπίστηκαν άλλες ευκαιρίες double chance")
    
    if dc_reasons and total >= 6:
        with st.expander("📊 Στατιστικά Στοιχεία", expanded=False):
            for reason in dc_reasons:
                st.markdown(f"- {reason}")
    
    if h_t > 0 and a_t > 0 and total >= 6:
        real_draw_pct = (st.session_state.hd + st.session_state.ad) / (h_t + a_t)
        away_draw_pct = st.session_state.ad / a_t if a_t > 0 else 0
        st.markdown(f"**📊 Πραγματικό ποσοστό ισοπαλίας:** {real_draw_pct*100:.1f}%")
        st.markdown(f"**📊 Φιλοξενούμενος ισοπαλίες εκτός:** {away_draw_pct*100:.1f}%")
    
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
        explanations = generate_explanation(p1, pX, p2, odd1, oddX, odd2, h_t, a_t, main_point, top_two, sorted_stats)
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
        
        # Υπολογισμοί για όλες τις περιπτώσεις
        prob_1X = p1 + pX
        prob_X2 = pX + p2
        prob_12 = p1 + p2
        
        implied_1X = 1 / (1/odd1 + 1/oddX) if odd1 > 1.0 and oddX > 1.0 else 0
        implied_X2 = 1 / (1/oddX + 1/odd2) if oddX > 1.0 and odd2 > 1.0 else 0
        implied_12 = 1 / (1/odd1 + 1/odd2) if odd1 > 1.0 and odd2 > 1.0 else 0
        
        # Δημιουργία πίνακα με όλες τις περιπτώσεις
        comp_data = {
            'Σημείο': ['1', 'X', '2', '1X', 'X2', '12'],
            'Απόδοση': [
                f"{odd1:.2f}", 
                f"{oddX:.2f}", 
                f"{odd2:.2f}",
                f"{implied_1X:.2f}",
                f"{implied_X2:.2f}", 
                f"{implied_12:.2f}"
            ],
            'Μοντέλο': [
                f"{p1*100:.1f}%", 
                f"{pX*100:.1f}%", 
                f"{p2*100:.1f}%",
                f"{prob_1X*100:.1f}%",
                f"{prob_X2*100:.1f}%", 
                f"{prob_12*100:.1f}%"
            ],
            'Bookie': [
                f"{1/odd1*100:.1f}%", 
                f"{1/oddX*100:.1f}%", 
                f"{1/odd2*100:.1f}%",
                f"{1/implied_1X*100:.1f}%",
                f"{1/implied_X2*100:.1f}%", 
                f"{1/implied_12*100:.1f}%"
            ],
            'Διαφορά': [
                f"{p1*100 - 1/odd1*100:+.1f}%", 
                f"{pX*100 - 1/oddX*100:+.1f}%", 
                f"{p2*100 - 1/odd2*100:+.1f}%",
                f"{prob_1X*100 - 1/implied_1X*100:+.1f}%",
                f"{prob_X2*100 - 1/implied_X2*100:+.1f}%", 
                f"{prob_12*100 - 1/implied_12*100:+.1f}%"
            ]
        }
        
        st.dataframe(comp_data, use_container_width=True, hide_index=True)
        
        st.markdown("---")
        st.markdown("### 💡 Συμβουλή Διαχείρισης Ρίσκου")
        st.info(get_risk_advice(p1, pX, p2, conf, total, top_two_prob, main_point, top_two))
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
st.caption("BetAnalyzer v17.3.8 - Πλήρης ανάλυση με οπτική ιεράρχηση")
