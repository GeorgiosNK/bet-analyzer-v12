import streamlit as st
import plotly.graph_objects as go
import streamlit.components.v1 as components
import math

# ==============================
# CONFIG
# ==============================
st.set_page_config(page_title="Soccer Match Analyzer v5.0", page_icon="⚽", layout="centered")

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
.disagreement-box {
    background-color: #f8d7da; color: #721c24; padding: 12px;
    border-radius: 8px; border: 1px solid #f5c6cb; margin: 10px 0;
    font-weight: bold; text-align: center;
}
.trust-box {
    padding: 10px 15px; border-radius: 8px; margin: 10px 0;
    font-weight: bold; text-align: center; font-size: 0.9rem;
}
.dc-card {
    padding: 15px; border-radius: 10px; margin: 10px 0;
    border-left: 5px solid;
    transition: transform 0.2s;
}
.dc-card:hover { transform: translateX(5px); }
.main-proposal {
    font-size: 3.5rem; font-weight: 900; color: #1e3c72;
    line-height: 1.2; display: flex; align-items: center;
    justify-content: center; flex-wrap: wrap; gap: 10px;
}
.main-number { font-size: 3.5rem; font-weight: 900; color: #1e3c72; line-height: 1.2; }
.double-chance { font-size: 2.8rem; font-weight: 900; color: #1e3c72; line-height: 1.2; }
.double-percent { font-size: 1.6rem; font-weight: 600; margin-left: 5px; }
</style>
""", unsafe_allow_html=True)

# ==============================
# STATE INITIALIZATION
# ==============================
for key, val in [
    ('hw',0),('hd',0),('hl',0),('aw',0),('ad',0),('al',0),
    ('hw_total',0),('hd_total',0),('hl_total',0),
    ('aw_total',0),('ad_total',0),('al_total',0),
    ('o1',"1.00"),('ox',"1.00"),('o2',"1.00"),
    ('current_proposal',""),('odds_trust_level',""),
]:
    if key not in st.session_state:
        st.session_state[key] = val

def reset_all():
    for key, val in [
        ('hw',0),('hd',0),('hl',0),('aw',0),('ad',0),('al',0),
        ('hw_total',0),('hd_total',0),('hl_total',0),
        ('aw_total',0),('ad_total',0),('al_total',0),
        ('o1',"1.00"),('ox',"1.00"),('o2',"1.00"),
        ('current_proposal',""),('odds_trust_level',""),
    ]:
        st.session_state[key] = val

# ==============================
# SAFE FUNCTION FOR ODDS
# ==============================
def sf(x):
    try:
        v = float(str(x).replace(',','.'))
        return max(1.01, v)
    except:
        return 1.01

# ==============================
# [NEW v5] DIXON-COLES STYLE MODEL
# ==============================
def calculate_team_strengths(hw, hd, hl, aw, ad, al, h_t, a_t):
    """
    Υπολογίζει attack strength για κάθε ομάδα σε σχέση με league avg=1.0.
    Χρησιμοποιεί points-based proxy αντί για γκολ.
    """
    if h_t == 0 or a_t == 0:
        return 1.0, 1.0

    # Points per game (max 3)
    h_ppg = (hw * 3 + hd) / h_t
    a_ppg = (aw * 3 + ad) / a_t

    # League average
    league_avg = (h_ppg + a_ppg) / 2 if (h_ppg + a_ppg) > 0 else 1.5

    # Strength relative to average, clamped
    home_str = max(0.4, min(2.5, h_ppg / league_avg)) if league_avg > 0 else 1.0
    away_str = max(0.4, min(2.5, a_ppg / league_avg)) if league_avg > 0 else 1.0

    return home_str, away_str


def dixon_coles_probs(home_str, away_str, home_advantage=1.15):
    """
    Απλοποιημένο Dixon-Coles:
    - Home advantage factor ενσωματωμένο
    - Draw probability ανάλογο της ισορροπίας των ομάδων
    """
    h_eff = home_str * home_advantage
    a_eff = away_str
    total  = h_eff + a_eff

    raw_p1 = h_eff / total
    raw_p2 = a_eff / total

    # Draw: μεγαλύτερο όταν οι ομάδες είναι ισοδύναμες
    closeness = 1.0 - abs(raw_p1 - raw_p2)   # 0=πολύ διαφορετικές, 1=ίσες
    base_draw = 0.28 * (closeness ** 1.5)     # max ~28%

    p1 = raw_p1 * (1.0 - base_draw)
    p2 = raw_p2 * (1.0 - base_draw)
    pX = base_draw

    s = p1 + pX + p2
    return p1/s, pX/s, p2/s


# ==============================
# [NEW v5] DRAW LIKELIHOOD SCORE
# ==============================
def calculate_draw_likelihood(hw, hd, hl, aw, ad, al, h_t, a_t,
                               hw_total, hd_total, hl_total,
                               aw_total, ad_total, al_total,
                               h_total_t, a_total_t):
    """
    Επιστρέφει draw_factor:
      >1.0 = πιθανότερη ισοπαλία
      <1.0 = λιγότερο πιθανή
    Αντικαθιστά τα hardcoded thresholds.
    """
    factors = []

    # 1. Recent draw rate (τελευταία 5)
    if h_t > 0 and a_t > 0:
        recent_draw_rate = (hd + ad) / (h_t + a_t)
        factors.append(recent_draw_rate / 0.27)  # 0.27 = league avg

    # 2. Historical draw rate
    if h_total_t >= 10 and a_total_t >= 10:
        hist_draw_rate = (hd_total + ad_total) / (h_total_t + a_total_t)
        factors.append(hist_draw_rate / 0.27)

    # 3. Αμφότερες draw-prone
    if h_t > 0 and a_t > 0:
        h_draw_pct = hd / h_t
        a_draw_pct = ad / a_t
        if h_draw_pct > 0.30 and a_draw_pct > 0.30:
            factors.append(1.30)
        elif h_draw_pct < 0.15 and a_draw_pct < 0.15:
            factors.append(0.55)

    # 4. Ισορροπία δυνάμεων
    if h_t > 0 and a_t > 0:
        h_pts = (hw * 3 + hd) / h_t
        a_pts = (aw * 3 + ad) / a_t
        max_pts = max(h_pts, a_pts, 0.01)
        balance = 1.0 - min(1.0, abs(h_pts - a_pts) / max_pts)
        factors.append(0.70 + 0.60 * balance)  # [0.70, 1.30]

    if not factors:
        return 1.0

    # Geometric mean (πιο σταθερό από arithmetic)
    geo_mean = math.exp(sum(math.log(max(f, 0.01)) for f in factors) / len(factors))
    return max(0.35, min(2.0, geo_mean))


# ==============================
# [NEW v5] GRADUATED TRUST SYSTEM
# ==============================
def calculate_odds_trust(stat_p1, stat_pX, stat_p2,
                          norm_implied_1, norm_implied_X, norm_implied_2,
                          total):
    """
    Graduated trust: αντί για binary bypass,
    επιστρέφει odds_weight (0.05 - 0.30) ανάλογα με τη συμφωνία.
    """
    disagreements = [
        abs(stat_p1 - norm_implied_1),
        abs(stat_pX - norm_implied_X),
        abs(stat_p2 - norm_implied_2),
    ]
    max_dis = max(disagreements)

    sample_trust = min(1.0, total / 15.0)

    if max_dis > 0.25 and total >= 8:
        odds_weight = 0.05
        trust_level = "🔴 ΧΑΜΗΛΗ"
        message = (f"Μεγάλη ασυμφωνία στατιστικών-αποδόσεων ({max_dis*100:.0f}%). "
                   f"Βάρος αποδόσεων: 5% — Ανάλυση βασισμένη κυρίως σε στατιστικά.")
        bg = "#f8d7da"; fg = "#721c24"
    elif max_dis > 0.15 and total >= 6:
        odds_weight = 0.15
        trust_level = "🟡 ΜΕΤΡΙΑ"
        message = (f"Μέτρια ασυμφωνία ({max_dis*100:.0f}%). "
                   f"Βάρος αποδόσεων: 15%.")
        bg = "#fff3cd"; fg = "#856404"
    else:
        odds_weight = max(0.20, 0.30 * (1 - sample_trust * 0.25))
        trust_level = "🟢 ΥΨΗΛΗ"
        message = (f"Καλή συμφωνία στατιστικών-αποδόσεων. "
                   f"Βάρος αποδόσεων: {odds_weight*100:.0f}%.")
        bg = "#d4edda"; fg = "#155724"

    return odds_weight, trust_level, message, bg, fg


# ==============================
# [NEW v5] CONFIDENCE CALCULATION
# ==============================
def calculate_confidence(p1, pX, p2, total):
    """
    Confidence βασισμένο σε 3 παράγοντες:
    1. Separation: πόσο ξεχωρίζει το top outcome
    2. Sample size
    3. Entropy: πόσο ξεκάθαρη είναι η κατανομή
    """
    sorted_p = sorted([p1, pX, p2], reverse=True)

    # 1. Separation (top vs 2nd)
    separation = sorted_p[0] - sorted_p[1]
    separation_score = min(1.0, separation / 0.25)

    # 2. Sample size
    sample_score = min(1.0, total / 20.0)

    # 3. Entropy-based consistency
    entropy = -sum(p * math.log(max(p, 1e-9)) for p in [p1, pX, p2])
    max_entropy = math.log(3)
    consistency_score = 1.0 - (entropy / max_entropy)

    raw_conf = (
        0.45 * separation_score +
        0.30 * sample_score +
        0.25 * consistency_score
    )

    # Scale [20, 85]
    conf = int(20 + raw_conf * 65)
    return min(85, max(20, conf))


# ==============================
# DOUBLE CHANCE ANALYSIS
# ==============================
def analyze_double_chance(p1, pX, p2, odd1, oddX, odd2, h_t, a_t):
    recommendations = []

    prob_1X = p1 + pX
    prob_X2 = pX + p2
    prob_12 = p1 + p2

    implied_1X = 1 / (1/odd1 + 1/oddX) if odd1 > 1.01 and oddX > 1.01 else 0
    implied_X2 = 1 / (1/oddX + 1/odd2) if oddX > 1.01 and odd2 > 1.01 else 0
    implied_12 = 1 / (1/odd1 + 1/odd2) if odd1 > 1.01 and odd2 > 1.01 else 0

    home_losses = st.session_state.hl / h_t if h_t > 0 else 0.5
    away_losses = st.session_state.al / a_t if a_t > 0 else 0.5

    # 12 (no draw)
    if implied_12 > 0 and prob_12 > 0.80 and pX < 0.20:
        value = prob_12 - (1/implied_12)
        if value > 0.02:
            recommendations.append({
                'pick': '12', 'prob': prob_12*100, 'odds': implied_12,
                'value': value*100, 'risk': 'low',
                'reason': f"Σχεδόν σίγουρο όχι ισοπαλία — μόνο {pX*100:.1f}%"
            })

    # 1X
    if implied_1X > 0 and prob_1X > 0.65:
        value = prob_1X - (1/implied_1X)
        if implied_1X >= 1.80 and value > 0.03:
            recommendations.append({'pick':'1X','prob':prob_1X*100,'odds':implied_1X,'value':value*100,'risk':'high',
                'reason':f"Ελκυστική απόδοση {implied_1X:.2f} για {prob_1X*100:.0f}%"})
        elif implied_1X >= 1.50 and value > 0.05 and home_losses < 0.25:
            recommendations.append({'pick':'1X','prob':prob_1X*100,'odds':implied_1X,'value':value*100,'risk':'medium',
                'reason':f"Γηπεδούχος αήττητος σε {prob_1X*100:.0f}% (χάνει μόνο {home_losses*100:.0f}%)"})
        elif implied_1X >= 1.30 and prob_1X > 0.75 and home_losses < 0.15:
            recommendations.append({'pick':'1X','prob':prob_1X*100,'odds':implied_1X,'value':value*100,'risk':'low',
                'reason':f"Πολύ ασφαλές 1X — {prob_1X*100:.0f}% πιθανότητα"})

    # X2
    if implied_X2 > 0 and prob_X2 > 0.65:
        value = prob_X2 - (1/implied_X2)
        if implied_X2 >= 1.80 and value > 0.03:
            recommendations.append({'pick':'X2','prob':prob_X2*100,'odds':implied_X2,'value':value*100,'risk':'high',
                'reason':f"Ελκυστική απόδοση {implied_X2:.2f} για {prob_X2*100:.0f}%"})
        elif implied_X2 >= 1.50 and value > 0.05 and away_losses < 0.30:
            recommendations.append({'pick':'X2','prob':prob_X2*100,'odds':implied_X2,'value':value*100,'risk':'medium',
                'reason':f"Φιλοξενούμενος αήττητος σε {prob_X2*100:.0f}% (χάνει μόνο {away_losses*100:.0f}%)"})
        elif implied_X2 >= 1.30 and prob_X2 > 0.75 and away_losses < 0.20:
            recommendations.append({'pick':'X2','prob':prob_X2*100,'odds':implied_X2,'value':value*100,'risk':'low',
                'reason':f"Πολύ ασφαλές X2 — {prob_X2*100:.0f}% πιθανότητα"})

    return recommendations


def get_double_chance_reason(p1, pX, p2, h_t, a_t, hd_c, ad_c):
    reasons = []
    if h_t > 0:
        hl_r = st.session_state.hl / h_t
        hd_r = hd_c / h_t
        if hl_r < 0.15:
            reasons.append(f"🏠 Γηπεδούχος: Μόνο {hl_r*100:.0f}% ήττες εντός έδρας")
        if hd_r > 0.35:
            reasons.append(f"🤝 Γηπεδούχος: {hd_r*100:.0f}% ισοπαλίες")
    if a_t > 0:
        al_r = st.session_state.al / a_t
        ad_r = ad_c / a_t
        if al_r < 0.20:
            reasons.append(f"🚀 Φιλοξενούμενος: Μόνο {al_r*100:.0f}% ήττες εκτός")
        if ad_r > 0.35:
            reasons.append(f"🤝 Φιλοξενούμενος: {ad_r*100:.0f}% ισοπαλίες εκτός")
        if ad_r < 0.10 and a_t >= 10:
            reasons.append(f"⚡ Φιλοξενούμενος: ΜΟΝΟ {ad_r*100:.1f}% ισοπαλίες εκτός!")
    return reasons


# ==============================
# KEY METRICS & RISK ADVICE
# ==============================
def calculate_key_metrics(p1, pX, p2, odd1, oddX, odd2):
    p1 = max(0.01, min(0.99, p1))
    pX = max(0.01, min(0.99, pX))
    p2 = max(0.01, min(0.99, p2))
    odd1 = max(1.01, odd1)
    oddX = max(1.01, oddX)
    odd2 = max(1.01, odd2)

    imp_h = 1/odd1*100; imp_d = 1/oddX*100; imp_a = 1/odd2*100
    tot_i = imp_h + imp_d + imp_a
    imp_h /= tot_i/100; imp_d /= tot_i/100; imp_a /= tot_i/100

    edges = [p1*100 - imp_h, pX*100 - imp_d, p2*100 - imp_a]
    names = ['home_edge','draw_edge','away_edge']
    max_e = max(edges)
    return {
        'home_edge': edges[0], 'draw_edge': edges[1], 'away_edge': edges[2],
        'best_value': names[edges.index(max_e)], 'value_amount': max_e
    }


def get_risk_advice(p1, pX, p2, conf, total, top_two_prob, main_point, top_two):
    if total < 8:
        return "🔴 **ΑΝΕΠΑΡΚΗ ΔΕΔΟΜΕΝΑ**: Λιγότερα από 8 συνολικά παιχνίδια — Αποφυγή"
    if top_two_prob >= 80:
        return (f"🟢 **ΠΟΛΥ ΥΨΗΛΗ ΠΙΘΑΝΟΤΗΤΑ ΚΑΛΥΨΗΣ**: Η διπλή ευκαιρία {top_two} έχει "
                f"{top_two_prob:.1f}% — Ιδανικό για safe bet. Κύριο σημείο {main_point}: {conf}% confidence.")
    elif top_two_prob >= 70:
        return (f"🟡 **ΚΑΛΗ ΠΙΘΑΝΟΤΗΤΑ ΚΑΛΥΨΗΣ**: Η διπλή ευκαιρία {top_two} έχει "
                f"{top_two_prob:.1f}% — Κατάλληλο για normal bet. Κύριο σημείο {main_point}: {conf}% confidence.")
    if conf >= 65:
        return f"🟢 **Υψηλή εμπιστοσύνη**: Το {main_point} έχει {conf}% confidence — Κανονικό ποντάρισμα."
    elif conf >= 45:
        return (f"🟡 **Μέτρια εμπιστοσύνη**: Το {main_point} έχει {conf}% confidence — "
                f"Μείωση ποντάρισματος ή προτίμηση διπλής ευκαιρίας {top_two} ({top_two_prob:.1f}%).")
    else:
        return f"🔴 **Χαμηλή εμπιστοσύνη**: Το {main_point} έχει μόνο {conf}% confidence — Μικρό ποντάρισμα ή αποφυγή."


# ==============================
# SIDEBAR
# ==============================
with st.sidebar:
    st.header("🏆 Control Panel")
    st.button("🧹 Clear Stats & Odds", on_click=reset_all, use_container_width=True)

    st.markdown("### 💰 Αποδόσεις")
    o1_i = st.text_input("Άσος (1)", key="o1")
    ox_i = st.text_input("Ισοπαλία (X)", key="ox")
    o2_i = st.text_input("Διπλό (2)", key="o2")

    st.markdown("---")
    st.markdown("### 🏠 Γηπεδούχος (τελευταίοι 5 εντός)")
    st.number_input("Νίκες",     0, 100, key="hw")
    st.number_input("Ισοπαλίες", 0, 100, key="hd")
    st.number_input("Ήττες",     0, 100, key="hl")

    st.markdown("### 🚀 Φιλοξενούμενος (τελευταίοι 5 εκτός)")
    st.number_input("Νίκες εκτός",     0, 100, key="aw")
    st.number_input("Ισοπαλίες εκτός", 0, 100, key="ad")
    st.number_input("Ήττες εκτός",     0, 100, key="al")

    st.markdown("---")
    st.markdown("### 📊 ΣΥΝΟΛΙΚΑ ΣΤΑΤΙΣΤΙΚΑ")
    st.markdown("#### 🏠 Γηπεδούχος (Σύνολο εντός)")
    st.number_input("Νίκες (Σύνολο)",      0, 500, key="hw_total")
    st.number_input("Ισοπαλίες (Σύνολο)",  0, 500, key="hd_total")
    st.number_input("Ήττες (Σύνολο)",      0, 500, key="hl_total")

    st.markdown("#### 🚀 Φιλοξενούμενος (Σύνολο εκτός)")
    st.number_input("Νίκες εκτός (Σύνολο)",      0, 500, key="aw_total")
    st.number_input("Ισοπαλίες εκτός (Σύνολο)",  0, 500, key="ad_total")
    st.number_input("Ήττες εκτός (Σύνολο)",      0, 500, key="al_total")

odd1, oddX, odd2 = sf(o1_i), sf(ox_i), sf(o2_i)

# ==============================
# CALCULATIONS ENGINE
# ==============================
h_t = st.session_state.hw + st.session_state.hd + st.session_state.hl
a_t = st.session_state.aw + st.session_state.ad + st.session_state.al
total = h_t + a_t

h_total_t = st.session_state.hw_total + st.session_state.hd_total + st.session_state.hl_total
a_total_t = st.session_state.aw_total + st.session_state.ad_total + st.session_state.al_total
total_games_all = h_total_t + a_total_t

use_total_stats = h_total_t >= 10 and a_total_t >= 10

# ---- Combined stats (70% recent, 30% historical) ----
if use_total_stats:
    h_win_last5  = st.session_state.hw / h_t if h_t > 0 else 0
    h_draw_last5 = st.session_state.hd / h_t if h_t > 0 else 0
    a_win_last5  = st.session_state.aw / a_t if a_t > 0 else 0
    a_draw_last5 = st.session_state.ad / a_t if a_t > 0 else 0

    h_win_total  = st.session_state.hw_total / h_total_t
    h_draw_total = st.session_state.hd_total / h_total_t
    a_win_total  = st.session_state.aw_total / a_total_t
    a_draw_total = st.session_state.ad_total / a_total_t

    h_win_c  = 0.7*h_win_last5  + 0.3*h_win_total
    h_draw_c = 0.7*h_draw_last5 + 0.3*h_draw_total
    a_win_c  = 0.7*a_win_last5  + 0.3*a_win_total
    a_draw_c = 0.7*a_draw_last5 + 0.3*a_draw_total

    hw_c = h_win_c * h_t
    hd_c = h_draw_c * h_t
    hl_c = (1 - h_win_c - h_draw_c) * h_t
    aw_c = a_win_c * a_t
    ad_c = a_draw_c * a_t
    al_c = (1 - a_win_c - a_draw_c) * a_t
else:
    hw_c = st.session_state.hw
    hd_c = st.session_state.hd
    hl_c = st.session_state.hl
    aw_c = st.session_state.aw
    ad_c = st.session_state.ad
    al_c = st.session_state.al

# ---- Implied probabilities from odds ----
try:
    inv = 1/odd1 + 1/oddX + 1/odd2
    pm1 = (1/odd1)/inv if inv > 0 else 0.33
    pmX = (1/oddX)/inv if inv > 0 else 0.33
    pm2 = (1/odd2)/inv if inv > 0 else 0.33
except:
    pm1 = pmX = pm2 = 0.33

# ---- [NEW v5] Dixon-Coles stat probabilities ----
home_str, away_str = calculate_team_strengths(hw_c, hd_c, hl_c, aw_c, ad_c, al_c, h_t, a_t)
stat_p1, stat_pX, stat_p2 = dixon_coles_probs(home_str, away_str)

# ---- [NEW v5] Draw Likelihood adjustment ----
draw_factor = calculate_draw_likelihood(
    st.session_state.hw, st.session_state.hd, st.session_state.hl,
    st.session_state.aw, st.session_state.ad, st.session_state.al,
    h_t, a_t,
    st.session_state.hw_total, st.session_state.hd_total, st.session_state.hl_total,
    st.session_state.aw_total, st.session_state.ad_total, st.session_state.al_total,
    h_total_t, a_total_t
)
stat_pX_adj = stat_pX * draw_factor
stat_p1_adj = stat_p1 * (1 + (stat_pX - stat_pX_adj) * stat_p1 / (stat_p1 + stat_p2 + 1e-9))
stat_p2_adj = stat_p2 * (1 + (stat_pX - stat_pX_adj) * stat_p2 / (stat_p1 + stat_p2 + 1e-9))
s = stat_p1_adj + stat_pX_adj + stat_p2_adj
stat_p1, stat_pX, stat_p2 = stat_p1_adj/s, stat_pX_adj/s, stat_p2_adj/s

# ---- [NEW v5] Graduated Trust System ----
odds_weight, trust_level, trust_msg, trust_bg, trust_fg = calculate_odds_trust(
    stat_p1, stat_pX, stat_p2,
    pm1, pmX, pm2,
    total
)
stats_weight = 1.0 - odds_weight

# ---- Final blend ----
if total >= 6:
    alpha = min(stats_weight, total / 20.0 * stats_weight)
    p1 = alpha * stat_p1 + (1 - alpha) * pm1
    pX = alpha * stat_pX + (1 - alpha) * pmX
    p2 = alpha * stat_p2 + (1 - alpha) * pm2
else:
    p1, pX, p2 = pm1, pmX, pm2

# Clamp & normalize
p1 = max(0.05, p1); pX = max(0.05, pX); p2 = max(0.05, p2)
s = p1 + pX + p2
p1, pX, p2 = p1/s, pX/s, p2/s

# ==============================
# PROPOSAL & CONFIDENCE
# ==============================
stats_list = [("1", p1), ("X", pX), ("2", p2)]
sorted_stats = sorted(stats_list, key=lambda x: x[1], reverse=True)

main_point   = sorted_stats[0][0]
top_two      = sorted_stats[0][0] + sorted_stats[1][0]
top_two_prob = (sorted_stats[0][1] + sorted_stats[1][1]) * 100

dc_color = "#2ecc71" if top_two_prob >= 65 else "#f1c40f" if top_two_prob >= 45 else "#e74c3c"

proposal = ""
warning  = ""
conf     = 0
color    = "#95a5a6"

if total < 6:
    proposal   = "🚫 NO BET"
    warning    = "⚠️ ΑΝΕΠΑΡΚΗ ΣΤΑΤΙΣΤΙΚΑ: Χρειάζονται τουλάχιστον 6 συνολικά παιχνίδια"
    main_point = "🚫"
    top_two    = ""
    top_two_prob = 0
else:
    # [NEW v5] Entropy-based confidence
    conf = calculate_confidence(p1, pX, p2, total)

    # Cap confidence if low data
    if total < 10:
        conf = min(conf, 60)
        if total < 8:
            warning = "⚠️ ΜΕΙΩΜΕΝΗ ΑΞΙΟΠΙΣΤΙΑ: Λίγα στατιστικά δεδομένα"
    elif total < 15:
        conf = min(conf, 72)

    color = "#2ecc71" if conf >= 65 else "#f1c40f" if conf >= 45 else "#e74c3c"

    if pX * 100 < 15:
        warning = (f"📊 ΣΤΑΤΙΣΤΙΚΗ ΠΑΡΑΤΗΡΗΣΗ: Ισοπαλία πολύ χαμηλή στο μοντέλο "
                   f"({pX*100:.1f}%). Πρόταση {top_two} βασίζεται στα δύο επικρατέστερα.")
    elif pX * 100 < 20:
        warning = (f"📊 ΣΤΑΤΙΣΤΙΚΗ ΠΑΡΑΤΗΡΗΣΗ: Ισοπαλία στο {pX*100:.1f}%. "
                   f"Πρόταση {top_two} επιλέχθηκε ως κάλυψη.")

st.session_state.current_proposal = f"{main_point} ({top_two})"

# ==============================
# UI OUTPUT
# ==============================
if total >= 6:
    st.markdown(f"""
    <div class="result-card">
        <div style="color:gray;font-weight:bold;margin-bottom:5px;">📊 Soccer Match Analyzer v5.0</div>
        <div class="main-proposal">
            <span class="main-number">{main_point}</span>
            <span class="double-chance">({top_two} <span class="double-percent" style="color:{dc_color};">{top_two_prob:.1f}%</span>)</span>
        </div>
        <div style="font-size:1.8rem;font-weight:bold;color:{color};margin-top:10px;">{conf}% Confidence</div>
        <div style="margin-top:15px;font-family:monospace;font-size:1rem;color:#555;">
            [MODEL]: 1: {p1*100:.1f}% | X: {pX*100:.1f}% | 2: {p2*100:.1f}%
        </div>
    """, unsafe_allow_html=True)

    if use_total_stats:
        st.markdown(f"""
        <div style="font-size:0.9rem;color:#666;margin-top:5px;text-align:center;">
            📈 Συνδυασμός: 70% τελευταία 5 + 30% σύνολο ({total_games_all} αγώνες)
        </div>
        """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)
else:
    st.markdown(f"""
    <div class="result-card">
        <div style="color:gray;font-weight:bold;margin-bottom:5px;">📊 Soccer Match Analyzer v5.0</div>
        <div class="main-proposal"><span class="main-number">{main_point}</span></div>
        <div style="font-size:1.8rem;font-weight:bold;color:{color};margin-top:10px;">{conf}% Confidence</div>
    </div>
    """, unsafe_allow_html=True)

# Trust level badge
if total >= 6:
    st.markdown(
        f'<div class="trust-box" style="background:{trust_bg};color:{trust_fg};">'
        f'<b>Αξιοπιστία Αποδόσεων: {trust_level}</b> — {trust_msg}</div>',
        unsafe_allow_html=True
    )
elif warning:
    st.markdown(f'<div class="warning-box">{warning}</div>', unsafe_allow_html=True)

if warning and total >= 6:
    st.markdown(f'<div class="warning-box">{warning}</div>', unsafe_allow_html=True)

# ==============================
# DOUBLE CHANCE ANALYSIS
# ==============================
with st.expander("🛡️ Double Chance Analysis", expanded=False):
    dc_recommendations = analyze_double_chance(p1, pX, p2, odd1, oddX, odd2, h_t, a_t)
    dc_reasons = get_double_chance_reason(p1, pX, p2, h_t, a_t, hd_c, ad_c)

    if total >= 6:
        st.markdown("### 📊 Ανάλυση Πρότασης")
        st.markdown(f"""
        - **Κύριο σημείο:** {main_point} ({sorted_stats[0][1]*100:.1f}%)
        - **Διπλή ευκαιρία:** {top_two} ({top_two_prob:.1f}%)
        - **Draw factor (v5):** {draw_factor:.2f} {'📈 Ευνοεί ισοπαλία' if draw_factor>1.1 else '📉 Απομακρύνει ισοπαλία' if draw_factor<0.9 else '⚖️ Ουδέτερο'}
        """)

    if dc_recommendations and total >= 6:
        st.markdown("### 🎯 Double Chance Opportunities")
        for rec in dc_recommendations:
            if rec['pick'] != top_two:
                bg_color    = "#e8f5e9" if rec['odds'] >= 1.80 else "#fff3e0" if rec['odds'] >= 1.50 else "#e3f2fd"
                border_color = "#2ecc71" if rec['odds'] >= 1.80 else "#f39c12" if rec['odds'] >= 1.50 else "#3498db"
                value_text  = f"🔥 +{rec['value']:.1f}%" if rec['value']>10 else f"📈 +{rec['value']:.1f}%" if rec['value']>5 else f"⚖️ +{rec['value']:.1f}%"
                value_color = "#2ecc71" if rec['value']>10 else "#f1c40f" if rec['value']>5 else "#95a5a6"
                risk_label  = "🔴 Υψηλό" if rec['risk']=='high' else "🟡 Μέτριο" if rec['risk']=='medium' else "🟢 Χαμηλό"
                st.markdown(f"""
                <div class="dc-card" style="background-color:{bg_color};border-left-color:{border_color};">
                    <div style="display:flex;justify-content:space-between;align-items:center;">
                        <div>
                            <span style="font-size:2rem;font-weight:bold;color:#1e3c72;">{rec['pick']}</span>
                            <span style="font-size:1.2rem;margin-left:10px;background:white;padding:3px 10px;border-radius:15px;">{rec['prob']:.1f}%</span>
                        </div>
                        <div style="text-align:right;">
                            <div style="font-size:1.8rem;font-weight:bold;">{rec['odds']:.2f}</div>
                            <div style="color:{value_color};">{value_text}</div>
                        </div>
                    </div>
                    <div style="margin-top:10px;color:#34495e;">📌 {rec['reason']}</div>
                    <div style="margin-top:5px;font-size:0.9rem;">Ρίσκο: {risk_label}</div>
                </div>
                """, unsafe_allow_html=True)
    else:
        if total < 6:
            st.info("ℹ️ Ανεπαρκή δεδομένα για ανάλυση double chance")
        else:
            st.info("ℹ️ Δεν εντοπίστηκαν άλλες ευκαιρίες double chance")

    if dc_reasons and total >= 6:
        with st.expander("📊 Στατιστικά Στοιχεία", expanded=False):
            for r in dc_reasons:
                st.markdown(f"- {r}")

    if h_t > 0 and a_t > 0 and total >= 6:
        real_draw_pct = (hd_c + ad_c) / (h_t + a_t)
        away_draw_pct = ad_c / a_t if a_t > 0 else 0
        st.markdown(f"**📊 Ποσοστό Χ στο μοντέλο:** {pX*100:.1f}%")
        st.markdown(f"**📊 Πραγματικό ποσοστό ισοπαλίας:** {real_draw_pct*100:.1f}%")
        st.markdown(f"**📊 Φιλοξενούμενος ισοπαλίες εκτός:** {away_draw_pct*100:.1f}%")
        st.markdown(f"**📊 Draw Factor (v5):** {draw_factor:.3f}")

    st.markdown("---")
    st.markdown("""
    **💡 Double Chance Tips:**
    - 🟢 **Χαμηλό ρίσκο**: Αποδόσεις 1.30-1.50, >75% πιθανότητα
    - 🟡 **Μέτριο ρίσκο**: Αποδόσεις 1.50-1.80, >70% πιθανότητα
    - 🔴 **Υψηλό ρίσκο**: Αποδόσεις 1.80+, >65% πιθανότητα + value
    - ⚡ **12 (όχι ισοπαλία)**: Όταν ισοπαλία <15% στο μοντέλο
    """)

# ==============================
# ANALYTICAL EXPLANATIONS
# ==============================
with st.expander("🔍 Αναλυτική Εξήγηση Πρόβλεψης", expanded=False):
    if total >= 6:
        metrics = calculate_key_metrics(p1, pX, p2, odd1, oddX, odd2)

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### 📋 Παράγοντες Πρόβλεψης")
            st.markdown(f"- 🏠 **Home Strength:** {home_str:.2f}")
            st.markdown(f"- 🚀 **Away Strength:** {away_str:.2f}")
            st.markdown(f"- 🤝 **Draw Factor:** {draw_factor:.2f}")
            st.markdown(f"- 📊 **Odds Trust:** {trust_level} ({odds_weight*100:.0f}% βάρος)")

        with col2:
            st.markdown("### ⚖️ Value Analysis")
            value_map = {'home_edge':'Άσος (1)','draw_edge':'Ισοπαλία (Χ)','away_edge':'Διπλό (2)'}
            va = metrics.get('value_amount', 0)
            bv = metrics.get('best_value', 'home_edge')
            if abs(va) > 5:
                if va > 0:
                    st.markdown(f"✅ **Value bet**: +{va:.1f}% στο {value_map[bv]}")
                else:
                    st.markdown(f"❌ **Υπερτιμημένο**: {va:.1f}% στο {value_map[bv]}")
            else:
                st.markdown(f"⚖️ **Δίκαιη απόδοση**: {va:.1f}% διαφορά")

        st.markdown("---")
        st.markdown("### 📈 Αναλυτική Σύγκριση Πιθανοτήτων")

        prob_1X = p1 + pX; prob_X2 = pX + p2; prob_12 = p1 + p2
        imp_1X = 1/(1/odd1+1/oddX) if odd1>1.01 and oddX>1.01 else 0
        imp_X2 = 1/(1/oddX+1/odd2) if oddX>1.01 and odd2>1.01 else 0
        imp_12 = 1/(1/odd1+1/odd2) if odd1>1.01 and odd2>1.01 else 0

        comp_data = {
            'Σημείο': ['1','X','2','1X','X2','12'],
            'Απόδοση': [f"{odd1:.2f}",f"{oddX:.2f}",f"{odd2:.2f}",
                        f"{imp_1X:.2f}" if imp_1X>0 else "-",
                        f"{imp_X2:.2f}" if imp_X2>0 else "-",
                        f"{imp_12:.2f}" if imp_12>0 else "-"],
            'Μοντέλο': [f"{p1*100:.1f}%",f"{pX*100:.1f}%",f"{p2*100:.1f}%",
                        f"{prob_1X*100:.1f}%",f"{prob_X2*100:.1f}%",f"{prob_12*100:.1f}%"],
            'Bookie':  [f"{1/odd1*100:.1f}%",f"{1/oddX*100:.1f}%",f"{1/odd2*100:.1f}%",
                        f"{1/imp_1X*100:.1f}%" if imp_1X>0 else "-",
                        f"{1/imp_X2*100:.1f}%" if imp_X2>0 else "-",
                        f"{1/imp_12*100:.1f}%" if imp_12>0 else "-"],
            'Διαφορά': [f"{p1*100-1/odd1*100:+.1f}%",f"{pX*100-1/oddX*100:+.1f}%",f"{p2*100-1/odd2*100:+.1f}%",
                        f"{prob_1X*100-1/imp_1X*100:+.1f}%" if imp_1X>0 else "-",
                        f"{prob_X2*100-1/imp_X2*100:+.1f}%" if imp_X2>0 else "-",
                        f"{prob_12*100-1/imp_12*100:+.1f}%" if imp_12>0 else "-"],
        }
        st.dataframe(comp_data, use_container_width=True, hide_index=True)

        st.markdown("---")
        st.markdown("### 💡 Συμβουλή Διαχείρισης Ρίσκου")
        st.info(get_risk_advice(p1, pX, p2, conf, total, top_two_prob, main_point, top_two))
    else:
        st.info("ℹ️ Ανεπαρκή δεδομένα (χρειάζονται ≥6 παιχνίδια)")

st.markdown("---")

# ==============================
# MAIN BAR CHART
# ==============================
if total >= 6:
    fig = go.Figure()
    fig.add_trace(go.Bar(
        name='Bookie %', x=['1','X','2'], y=[pm1*100, pmX*100, pm2*100],
        marker_color='#1e3c72',
        text=[f"<b>{pm1*100:.1f}%</b>",f"<b>{pmX*100:.1f}%</b>",f"<b>{pm2*100:.1f}%</b>"],
        textposition='inside', textfont=dict(color="white", size=14)
    ))
    fig.add_trace(go.Bar(
        name='Model v5 %', x=['1','X','2'], y=[p1*100, pX*100, p2*100],
        marker_color='#2ecc71',
        text=[f"<b>{p1*100:.1f}%</b>",f"<b>{pX*100:.1f}%</b>",f"<b>{p2*100:.1f}%</b>"],
        textposition='inside', textfont=dict(color="white", size=14)
    ))
    fig.update_layout(
        barmode='group', height=350,
        xaxis=dict(type='category'),
        margin=dict(l=20, r=20, t=20, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("📊 Συμπλήρωσε τουλάχιστον 6 συνολικά παιχνίδια για το γράφημα")

# Footer
st.markdown("---")
st.caption(
    "Soccer Match Analyzer v5.0 — "
    "Dixon-Coles style model | Entropy-based confidence | "
    "Draw Likelihood Score | Graduated Trust System"
)
