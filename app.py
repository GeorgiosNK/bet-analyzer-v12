import streamlit as st
import plotly.graph_objects as go
import streamlit.components.v1 as components
import math

# ==============================
# CONFIG
# ==============================
st.set_page_config(page_title="Soccer Match Analyzer v5.2", page_icon="⚽", layout="centered")

# ==============================
# JS INPUT FIX
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
# CSS
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
.trust-box {
    padding: 10px 15px; border-radius: 8px; margin: 10px 0;
    font-weight: bold; text-align: center; font-size: 0.9rem;
}
.dc-card {
    padding: 15px; border-radius: 10px; margin: 10px 0;
    border-left: 5px solid; transition: transform 0.2s;
}
.dc-card:hover { transform: translateX(5px); }
.main-proposal {
    font-size: 3.5rem; font-weight: 900; color: #1e3c72;
    line-height: 1.2; display: flex; align-items: center;
    justify-content: center; flex-wrap: wrap; gap: 10px;
}
.main-number  { font-size: 3.5rem; font-weight: 900; color: #1e3c72; line-height: 1.2; }
.double-chance{ font-size: 2.8rem; font-weight: 900; color: #1e3c72; line-height: 1.2; }
.double-percent{ font-size: 1.6rem; font-weight: 600; margin-left: 5px; }
</style>
""", unsafe_allow_html=True)

# ==============================
# STATE
# ==============================
for key, val in [
    ('hw',0),('hd',0),('hl',0),('aw',0),('ad',0),('al',0),
    ('hw_total',0),('hd_total',0),('hl_total',0),
    ('aw_total',0),('ad_total',0),('al_total',0),
    ('o1',"1.00"),('ox',"1.00"),('o2',"1.00"),
    ('current_proposal',""),
]:
    if key not in st.session_state:
        st.session_state[key] = val

def reset_all():
    for key, val in [
        ('hw',0),('hd',0),('hl',0),('aw',0),('ad',0),('al',0),
        ('hw_total',0),('hd_total',0),('hl_total',0),
        ('aw_total',0),('ad_total',0),('al_total',0),
        ('o1',"1.00"),('ox',"1.00"),('o2',"1.00"),
        ('current_proposal',""),
    ]:
        st.session_state[key] = val

def sf(x):
    try:
        v = float(str(x).replace(',','.'))
        return max(1.01, v)
    except:
        return 1.01

# ==============================
# [v5.2] GEOMETRIC STATS MODEL
# ==============================
def calculate_stat_probs(hw_c, hd_c, aw_c, ad_c, h_t, a_t):
    """
    Υπολογίζει p1/pX/p2 από combined stats.

    Λογική:
    - p(home win) ∝ sqrt( home_win_rate × away_loss_rate ) × home_advantage
    - p(away win) ∝ sqrt( away_win_rate × home_loss_rate )
    - p(draw)     = avg draw rate των δύο ομάδων

    Το draw% αντλείται ΑΠΕΥΘΕΙΑΣ από τα στατιστικά (draw affinity),
    όχι έμμεσα μέσω 1-p1-p2. Έτσι draw-prone ομάδες αναγνωρίζονται σωστά.
    """
    if h_t == 0 or a_t == 0:
        return 0.33, 0.34, 0.33

    h_win_r  = hw_c / h_t
    h_draw_r = hd_c / h_t
    h_loss_r = max(0.0, 1.0 - h_win_r - h_draw_r)

    a_win_r  = aw_c / a_t
    a_draw_r = ad_c / a_t
    a_loss_r = max(0.0, 1.0 - a_win_r - a_draw_r)

    # Draw = geometric mean των δύο draw rates
    raw_pX = math.sqrt(max(h_draw_r, 0.01) * max(a_draw_r, 0.01))

    # Win probs: geometric mean (αποφεύγει extreme τιμές)
    raw_p1 = math.sqrt(max(h_win_r, 0.01) * max(a_loss_r, 0.01)) * 1.08  # home advantage
    raw_p2 = math.sqrt(max(a_win_r, 0.01) * max(h_loss_r, 0.01))

    s = raw_p1 + raw_pX + raw_p2
    if s <= 0:
        return 0.33, 0.34, 0.33

    return raw_p1/s, raw_pX/s, raw_p2/s


# ==============================
# [v5.2] HISTORICAL DRAW FINE-TUNE
# ==============================
def get_historical_draw_factor(hd_total, h_total_t, ad_total, a_total_t):
    """
    Μικρή διόρθωση pX βάσει ιστορικού draw rate.
    Range: [0.80, 1.20] — δεν αντικαθιστά το geometric model.
    """
    if h_total_t < 10 or a_total_t < 10:
        return 1.0
    LEAGUE_AVG = 0.26
    hist_draw = (hd_total + ad_total) / (h_total_t + a_total_t)
    return max(0.80, min(1.20, hist_draw / LEAGUE_AVG))


# ==============================
# [v5] GRADUATED TRUST SYSTEM
# ==============================
def calculate_odds_trust(stat_p1, stat_pX, stat_p2, pm1, pmX, pm2, total):
    """
    Επιστρέφει odds_weight (0.05–0.30) ανάλογα με τη συμφωνία stats-αποδόσεων.
    """
    max_dis = max(abs(stat_p1-pm1), abs(stat_pX-pmX), abs(stat_p2-pm2))
    sample_trust = min(1.0, total / 15.0)

    if max_dis > 0.25 and total >= 8:
        odds_weight = 0.05
        trust_level = "🔴 ΧΑΜΗΛΗ"
        msg = (f"Μεγάλη ασυμφωνία στατιστικών-αποδόσεων ({max_dis*100:.0f}%). "
               f"Βάρος αποδόσεων: 5% — Ανάλυση βασισμένη κυρίως σε στατιστικά.")
        bg, fg = "#f8d7da", "#721c24"
    elif max_dis > 0.15 and total >= 6:
        odds_weight = 0.15
        trust_level = "🟡 ΜΕΤΡΙΑ"
        msg = f"Μέτρια ασυμφωνία ({max_dis*100:.0f}%). Βάρος αποδόσεων: 15%."
        bg, fg = "#fff3cd", "#856404"
    else:
        odds_weight = max(0.20, 0.30 * (1 - sample_trust * 0.25))
        trust_level = "🟢 ΥΨΗΛΗ"
        msg = f"Καλή συμφωνία στατιστικών-αποδόσεων. Βάρος αποδόσεων: {odds_weight*100:.0f}%."
        bg, fg = "#d4edda", "#155724"

    return odds_weight, trust_level, msg, bg, fg


# ==============================
# [v5] ENTROPY-BASED CONFIDENCE
# ==============================
def calculate_confidence(p1, pX, p2, total):
    """
    Confidence από 3 παράγοντες: separation, sample size, entropy.
    Κλίμακα [20, 85].
    """
    sorted_p = sorted([p1, pX, p2], reverse=True)
    separation_score = min(1.0, (sorted_p[0] - sorted_p[1]) / 0.25)
    sample_score     = min(1.0, total / 20.0)
    entropy = -sum(p * math.log(max(p, 1e-9)) for p in [p1, pX, p2])
    consistency_score = 1.0 - (entropy / math.log(3))
    raw = 0.45 * separation_score + 0.30 * sample_score + 0.25 * consistency_score
    return min(85, max(20, int(20 + raw * 65)))


# ==============================
# DOUBLE CHANCE ANALYSIS
# ==============================
def analyze_double_chance(p1, pX, p2, odd1, oddX, odd2, h_t, a_t):
    recs = []
    prob_1X = p1+pX; prob_X2 = pX+p2; prob_12 = p1+p2
    imp_1X = 1/(1/odd1+1/oddX) if odd1>1.01 and oddX>1.01 else 0
    imp_X2 = 1/(1/oddX+1/odd2) if oddX>1.01 and odd2>1.01 else 0
    imp_12 = 1/(1/odd1+1/odd2) if odd1>1.01 and odd2>1.01 else 0
    hl_r = st.session_state.hl/h_t if h_t>0 else 0.5
    al_r = st.session_state.al/a_t if a_t>0 else 0.5

    if imp_12>0 and prob_12>0.80 and pX<0.20:
        v = prob_12-(1/imp_12)
        if v>0.02: recs.append({'pick':'12','prob':prob_12*100,'odds':imp_12,'value':v*100,'risk':'low',
            'reason':f"Σχεδόν σίγουρο όχι ισοπαλία — μόνο {pX*100:.1f}%"})

    if imp_1X>0 and prob_1X>0.65:
        v=prob_1X-(1/imp_1X)
        if   imp_1X>=1.80 and v>0.03:
            recs.append({'pick':'1X','prob':prob_1X*100,'odds':imp_1X,'value':v*100,'risk':'high',
                'reason':f"Ελκυστική απόδοση {imp_1X:.2f} για {prob_1X*100:.0f}%"})
        elif imp_1X>=1.50 and v>0.05 and hl_r<0.25:
            recs.append({'pick':'1X','prob':prob_1X*100,'odds':imp_1X,'value':v*100,'risk':'medium',
                'reason':f"Γηπεδούχος αήττητος σε {prob_1X*100:.0f}% (χάνει μόνο {hl_r*100:.0f}%)"})
        elif imp_1X>=1.30 and prob_1X>0.75 and hl_r<0.15:
            recs.append({'pick':'1X','prob':prob_1X*100,'odds':imp_1X,'value':v*100,'risk':'low',
                'reason':f"Πολύ ασφαλές 1X — {prob_1X*100:.0f}%"})

    if imp_X2>0 and prob_X2>0.65:
        v=prob_X2-(1/imp_X2)
        if   imp_X2>=1.80 and v>0.03:
            recs.append({'pick':'X2','prob':prob_X2*100,'odds':imp_X2,'value':v*100,'risk':'high',
                'reason':f"Ελκυστική απόδοση {imp_X2:.2f} για {prob_X2*100:.0f}%"})
        elif imp_X2>=1.50 and v>0.05 and al_r<0.30:
            recs.append({'pick':'X2','prob':prob_X2*100,'odds':imp_X2,'value':v*100,'risk':'medium',
                'reason':f"Φιλοξενούμενος αήττητος σε {prob_X2*100:.0f}% (χάνει μόνο {al_r*100:.0f}%)"})
        elif imp_X2>=1.30 and prob_X2>0.75 and al_r<0.20:
            recs.append({'pick':'X2','prob':prob_X2*100,'odds':imp_X2,'value':v*100,'risk':'low',
                'reason':f"Πολύ ασφαλές X2 — {prob_X2*100:.0f}%"})
    return recs


def get_dc_reasons(hd_c, ad_c, h_t, a_t):
    reasons = []
    if h_t>0:
        hl_r=st.session_state.hl/h_t; hd_r=hd_c/h_t
        if hl_r<0.15: reasons.append(f"🏠 Γηπεδούχος: Μόνο {hl_r*100:.0f}% ήττες εντός")
        if hd_r>0.35: reasons.append(f"🤝 Γηπεδούχος: {hd_r*100:.0f}% ισοπαλίες εντός")
    if a_t>0:
        al_r=st.session_state.al/a_t; ad_r=ad_c/a_t
        if al_r<0.20: reasons.append(f"🚀 Φιλοξενούμενος: Μόνο {al_r*100:.0f}% ήττες εκτός")
        if ad_r>0.35: reasons.append(f"🤝 Φιλοξενούμενος: {ad_r*100:.0f}% ισοπαλίες εκτός")
        if ad_r<0.10 and a_t>=10: reasons.append(f"⚡ Φιλοξενούμενος: ΜΟΝΟ {ad_r*100:.1f}% ισοπαλίες εκτός!")
    return reasons


def calculate_key_metrics(p1, pX, p2, odd1, oddX, odd2):
    p1=max(0.01,min(0.99,p1)); pX=max(0.01,min(0.99,pX)); p2=max(0.01,min(0.99,p2))
    imp_h=1/odd1*100; imp_d=1/oddX*100; imp_a=1/odd2*100
    tot=imp_h+imp_d+imp_a
    imp_h/=tot/100; imp_d/=tot/100; imp_a/=tot/100
    edges=[p1*100-imp_h, pX*100-imp_d, p2*100-imp_a]
    names=['home_edge','draw_edge','away_edge']
    mx=max(edges)
    return {'home_edge':edges[0],'draw_edge':edges[1],'away_edge':edges[2],
            'best_value':names[edges.index(mx)],'value_amount':mx}


def get_risk_advice(conf, total, top_two_prob, main_point, top_two):
    if total<8:
        return "🔴 **ΑΝΕΠΑΡΚΗ ΔΕΔΟΜΕΝΑ**: Λιγότερα από 8 παιχνίδια — Αποφυγή"
    if top_two_prob>=80:
        return (f"🟢 **ΠΟΛΥ ΥΨΗΛΗ ΚΑΛΥΨΗ**: {top_two} έχει {top_two_prob:.1f}% — "
                f"Ιδανικό safe bet. Κύριο: {main_point} ({conf}% confidence).")
    elif top_two_prob>=70:
        return (f"🟡 **ΚΑΛΗ ΚΑΛΥΨΗ**: {top_two} έχει {top_two_prob:.1f}% — "
                f"Normal bet. Κύριο: {main_point} ({conf}% confidence).")
    if conf>=65:
        return f"🟢 **Υψηλή εμπιστοσύνη**: {main_point} — {conf}% confidence."
    elif conf>=45:
        return (f"🟡 **Μέτρια εμπιστοσύνη**: {main_point} — {conf}% confidence. "
                f"Προτιμήστε διπλή ευκαιρία {top_two} ({top_two_prob:.1f}%).")
    return f"🔴 **Χαμηλή εμπιστοσύνη**: {main_point} — μόνο {conf}%. Μικρό ποντάρισμα ή αποφυγή."


# ==============================
# SIDEBAR
# ==============================
with st.sidebar:
    st.header("🏆 Control Panel")
    st.button("🧹 Clear Stats & Odds", on_click=reset_all, use_container_width=True)

    st.markdown("### 💰 Αποδόσεις")
    o1_i = st.text_input("Άσος (1)",      key="o1")
    ox_i = st.text_input("Ισοπαλία (X)", key="ox")
    o2_i = st.text_input("Διπλό (2)",     key="o2")

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
    st.number_input("Νίκες (Σύνολο)",     0, 500, key="hw_total")
    st.number_input("Ισοπαλίες (Σύνολο)", 0, 500, key="hd_total")
    st.number_input("Ήττες (Σύνολο)",     0, 500, key="hl_total")

    st.markdown("#### 🚀 Φιλοξενούμενος (Σύνολο εκτός)")
    st.number_input("Νίκες εκτός (Σύνολο)",     0, 500, key="aw_total")
    st.number_input("Ισοπαλίες εκτός (Σύνολο)", 0, 500, key="ad_total")
    st.number_input("Ήττες εκτός (Σύνολο)",     0, 500, key="al_total")

odd1, oddX, odd2 = sf(o1_i), sf(ox_i), sf(o2_i)

# ==============================
# CALCULATIONS ENGINE
# ==============================
h_t    = st.session_state.hw + st.session_state.hd + st.session_state.hl
a_t    = st.session_state.aw + st.session_state.ad + st.session_state.al
total  = h_t + a_t

h_total_t     = st.session_state.hw_total + st.session_state.hd_total + st.session_state.hl_total
a_total_t     = st.session_state.aw_total + st.session_state.ad_total + st.session_state.al_total
total_games_all = h_total_t + a_total_t
use_total_stats = h_total_t >= 10 and a_total_t >= 10

# ---- Combined 70% recent + 30% historical ----
if use_total_stats:
    h_win_c  = 0.7*(st.session_state.hw/h_t)  + 0.3*(st.session_state.hw_total/h_total_t) if h_t>0 else 0
    h_draw_c = 0.7*(st.session_state.hd/h_t)  + 0.3*(st.session_state.hd_total/h_total_t) if h_t>0 else 0
    a_win_c  = 0.7*(st.session_state.aw/a_t)  + 0.3*(st.session_state.aw_total/a_total_t) if a_t>0 else 0
    a_draw_c = 0.7*(st.session_state.ad/a_t)  + 0.3*(st.session_state.ad_total/a_total_t) if a_t>0 else 0
else:
    h_win_c  = st.session_state.hw/h_t  if h_t>0 else 0
    h_draw_c = st.session_state.hd/h_t  if h_t>0 else 0
    a_win_c  = st.session_state.aw/a_t  if a_t>0 else 0
    a_draw_c = st.session_state.ad/a_t  if a_t>0 else 0

hw_c = h_win_c * h_t;  hd_c = h_draw_c * h_t
aw_c = a_win_c * a_t;  ad_c = a_draw_c * a_t

# ---- Implied probabilities from odds ----
try:
    inv = 1/odd1 + 1/oddX + 1/odd2
    pm1 = (1/odd1)/inv if inv>0 else 0.33
    pmX = (1/oddX)/inv if inv>0 else 0.33
    pm2 = (1/odd2)/inv if inv>0 else 0.33
except:
    pm1 = pmX = pm2 = 0.33

# ==============================
# [v5.2] CORE MODEL
# ==============================
if total >= 6:
    # Step 1: Geometric stat model (draw affinity built-in)
    stat_p1, stat_pX, stat_p2 = calculate_stat_probs(hw_c, hd_c, aw_c, ad_c, h_t, a_t)

    # Step 2: Historical draw fine-tune (small ±20% adjustment only)
    hist_factor = get_historical_draw_factor(
        st.session_state.hd_total, h_total_t,
        st.session_state.ad_total, a_total_t
    )
    stat_pX_adj = stat_pX * hist_factor
    extra = stat_pX - stat_pX_adj
    denom = max(stat_p1 + stat_p2, 0.001)
    stat_p1 = stat_p1 + extra * stat_p1 / denom
    stat_p2 = stat_p2 + extra * stat_p2 / denom
    stat_pX = stat_pX_adj
    s = stat_p1 + stat_pX + stat_p2
    stat_p1, stat_pX, stat_p2 = stat_p1/s, stat_pX/s, stat_p2/s

    # Step 3: Graduated trust — how much to weight odds vs stats
    odds_weight, trust_level, trust_msg, trust_bg, trust_fg = calculate_odds_trust(
        stat_p1, stat_pX, stat_p2, pm1, pmX, pm2, total
    )
    stats_weight = 1.0 - odds_weight
    alpha = min(stats_weight, total / 20.0 * stats_weight)

    # Step 4: Final blend
    p1 = alpha * stat_p1 + (1-alpha) * pm1
    pX = alpha * stat_pX + (1-alpha) * pmX
    p2 = alpha * stat_p2 + (1-alpha) * pm2
    p1=max(0.05,p1); pX=max(0.05,pX); p2=max(0.05,p2)
    s=p1+pX+p2; p1,pX,p2=p1/s,pX/s,p2/s
else:
    # Ανεπαρκή δεδομένα — χρησιμοποιούμε μόνο αποδόσεις
    p1, pX, p2 = pm1, pmX, pm2
    odds_weight, trust_level, trust_msg = 1.0, "", ""
    trust_bg, trust_fg = "#e2e3e5", "#383d41"
    stat_p1, stat_pX, stat_p2 = pm1, pmX, pm2
    hist_factor = 1.0

# ==============================
# PROPOSAL & CONFIDENCE
# ==============================
stats_list   = [("1",p1),("X",pX),("2",p2)]
sorted_stats = sorted(stats_list, key=lambda x: x[1], reverse=True)
main_point   = sorted_stats[0][0]

# [v5.3] Smart double chance:
# Αν 2ο και 3ο outcome είναι πολύ κοντά (<5%), η διπλή ευκαιρία
# καλύπτει 1ο + 3ο (πιο ασφαλής κάλυψη του αβέβαιου outcome)
gap_2nd_3rd = sorted_stats[1][1] - sorted_stats[2][1]
if gap_2nd_3rd < 0.05:
    top_two      = sorted_stats[0][0] + sorted_stats[2][0]
    top_two_prob = (sorted_stats[0][1] + sorted_stats[2][1]) * 100
    smart_dc     = True
else:
    top_two      = sorted_stats[0][0] + sorted_stats[1][0]
    top_two_prob = (sorted_stats[0][1] + sorted_stats[1][1]) * 100
    smart_dc     = False

dc_color = "#2ecc71" if top_two_prob>=80 else "#f1c40f" if top_two_prob>=60 else "#e74c3c"

warning = ""
conf    = 0
color   = "#95a5a6"

if total < 6:
    main_point   = "🚫"
    top_two      = ""
    top_two_prob = 0
    warning      = "⚠️ ΑΝΕΠΑΡΚΗ ΣΤΑΤΙΣΤΙΚΑ: Χρειάζονται τουλάχιστον 6 παιχνίδια"
else:
    conf  = calculate_confidence(p1, pX, p2, total)
    if total < 10: conf = min(conf, 60)
    elif total < 15: conf = min(conf, 72)
    if total < 8: warning = "⚠️ ΜΕΙΩΜΕΝΗ ΑΞΙΟΠΙΣΤΙΑ: Λίγα δεδομένα"
    color = "#2ecc71" if conf>=65 else "#f1c40f" if conf>=45 else "#e74c3c"

    if pX*100 < 15:
        warning = (f"📊 ΠΑΡΑΤΗΡΗΣΗ: Ισοπαλία πολύ χαμηλή ({pX*100:.1f}%). "
                   f"Πρόταση {top_two} βασίζεται στα δύο επικρατέστερα.")
    elif pX*100 < 20:
        warning = f"📊 ΠΑΡΑΤΗΡΗΣΗ: Ισοπαλία στο {pX*100:.1f}%. Πρόταση {top_two} ως κάλυψη."

st.session_state.current_proposal = f"{main_point} ({top_two})"

# ==============================
# UI OUTPUT — MAIN CARD
# ==============================
if total >= 6:
    smart_dc_label = f'<div style="font-size:0.85rem;color:#8e44ad;margin-top:5px;">⚡ Smart DC: 2ο &amp; 3ο outcome πολύ κοντά ({gap_2nd_3rd*100:.1f}% διαφορά)</div>' if smart_dc else ''
    st.markdown(f"""
    <div class="result-card">
        <div style="color:gray;font-weight:bold;margin-bottom:5px;">📊 Soccer Match Analyzer v5.4</div>
        <div class="main-proposal">
            <span class="main-number">{main_point}</span>
            <span class="double-chance">({top_two}&nbsp;<span class="double-percent" style="color:{dc_color};">{top_two_prob:.1f}%</span>)</span>
        </div>
        <div style="font-size:1.8rem;font-weight:bold;color:{color};margin-top:10px;">{conf}% Confidence</div>
        <div style="margin-top:15px;font-family:monospace;font-size:1rem;color:#555;">
            [MODEL]: 1: {p1*100:.1f}% | X: {pX*100:.1f}% | 2: {p2*100:.1f}%
        </div>
        {smart_dc_label}
    """, unsafe_allow_html=True)
    if use_total_stats:
        st.markdown(f"""
        <div style="font-size:0.9rem;color:#666;margin-top:5px;text-align:center;">
            📈 Συνδυασμός: 70% τελευταία 5 + 30% σύνολο ({total_games_all} αγώνες)
        </div>""", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
else:
    st.markdown(f"""
    <div class="result-card">
        <div style="color:gray;font-weight:bold;margin-bottom:5px;">📊 Soccer Match Analyzer v5.4</div>
        <div class="main-proposal"><span class="main-number">{main_point}</span></div>
        <div style="font-size:1.8rem;font-weight:bold;color:{color};margin-top:10px;">{conf}% Confidence</div>
    </div>""", unsafe_allow_html=True)

# Trust badge
if total >= 6 and trust_level:
    st.markdown(
        f'<div class="trust-box" style="background:{trust_bg};color:{trust_fg};">'
        f'<b>Αξιοπιστία Αποδόσεων: {trust_level}</b> — {trust_msg}</div>',
        unsafe_allow_html=True
    )
if warning:
    st.markdown(f'<div class="warning-box">{warning}</div>', unsafe_allow_html=True)

# ==============================
# DOUBLE CHANCE ANALYSIS
# ==============================
with st.expander("🛡️ Double Chance Analysis", expanded=False):
    dc_recs    = analyze_double_chance(p1, pX, p2, odd1, oddX, odd2, h_t, a_t)
    dc_reasons = get_dc_reasons(hd_c, ad_c, h_t, a_t)

    if total >= 6:
        st.markdown("### 📊 Ανάλυση Πρότασης")
        h_draw_disp = hd_c/h_t if h_t>0 else 0
        a_draw_disp = ad_c/a_t if a_t>0 else 0
        st.markdown(f"""
        - **Κύριο σημείο:** {main_point} ({sorted_stats[0][1]*100:.1f}%)
        - **Διπλή ευκαιρία:** {top_two} ({top_two_prob:.1f}%)
        - **Draw affinity:** Γηπεδούχος {h_draw_disp*100:.0f}% | Φιλοξενούμενος {a_draw_disp*100:.0f}%
        - **Ιστορικό draw factor:** {hist_factor:.2f} {'📈' if hist_factor>1.05 else '📉' if hist_factor<0.95 else '⚖️'}
        """)

    if dc_recs and total >= 6:
        st.markdown("### 🎯 Double Chance Opportunities")
        for rec in dc_recs:
            if rec['pick'] != top_two:
                bg_c = "#e8f5e9" if rec['odds']>=1.80 else "#fff3e0" if rec['odds']>=1.50 else "#e3f2fd"
                br_c = "#2ecc71" if rec['odds']>=1.80 else "#f39c12" if rec['odds']>=1.50 else "#3498db"
                vt   = f"🔥 +{rec['value']:.1f}%" if rec['value']>10 else f"📈 +{rec['value']:.1f}%" if rec['value']>5 else f"⚖️ +{rec['value']:.1f}%"
                vc   = "#2ecc71" if rec['value']>10 else "#f1c40f" if rec['value']>5 else "#95a5a6"
                rl   = "🔴 Υψηλό" if rec['risk']=='high' else "🟡 Μέτριο" if rec['risk']=='medium' else "🟢 Χαμηλό"
                st.markdown(f"""
                <div class="dc-card" style="background:{bg_c};border-left-color:{br_c};">
                    <div style="display:flex;justify-content:space-between;align-items:center;">
                        <div>
                            <span style="font-size:2rem;font-weight:bold;color:#1e3c72;">{rec['pick']}</span>
                            <span style="font-size:1.2rem;margin-left:10px;background:white;padding:3px 10px;border-radius:15px;">{rec['prob']:.1f}%</span>
                        </div>
                        <div style="text-align:right;">
                            <div style="font-size:1.8rem;font-weight:bold;">{rec['odds']:.2f}</div>
                            <div style="color:{vc};">{vt}</div>
                        </div>
                    </div>
                    <div style="margin-top:10px;color:#34495e;">📌 {rec['reason']}</div>
                    <div style="margin-top:5px;font-size:0.9rem;">Ρίσκο: {rl}</div>
                </div>""", unsafe_allow_html=True)
    elif total < 6:
        st.info("ℹ️ Ανεπαρκή δεδομένα για ανάλυση double chance")
    else:
        st.info("ℹ️ Δεν εντοπίστηκαν άλλες ευκαιρίες double chance")

    if dc_reasons and total >= 6:
        with st.expander("📊 Στατιστικά Στοιχεία", expanded=False):
            for r in dc_reasons:
                st.markdown(f"- {r}")

    if h_t>0 and a_t>0 and total>=6:
        real_draw = (hd_c+ad_c)/(h_t+a_t)
        st.markdown(f"**📊 Ποσοστό X στο μοντέλο:** {pX*100:.1f}%")
        st.markdown(f"**📊 Πραγματικό draw rate (combined):** {real_draw*100:.1f}%")
        st.markdown(f"**📊 Ιστορικό draw factor:** {hist_factor:.3f}")

    st.markdown("---")
    st.markdown("""
    **💡 Double Chance Tips:**
    - 🟢 **Χαμηλό ρίσκο**: Αποδόσεις 1.30-1.50, >75% πιθανότητα
    - 🟡 **Μέτριο ρίσκο**: Αποδόσεις 1.50-1.80, >70% πιθανότητα
    - 🔴 **Υψηλό ρίσκο**: Αποδόσεις 1.80+, >65% πιθανότητα + value
    - ⚡ **12 (όχι ισοπαλία)**: Όταν X <15% στο μοντέλο
    """)

# ==============================
# ANALYTICAL EXPLANATION
# ==============================
with st.expander("🔍 Αναλυτική Εξήγηση Πρόβλεψης", expanded=False):
    if total >= 6:
        metrics = calculate_key_metrics(p1, pX, p2, odd1, oddX, odd2)
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### 📋 Παράγοντες Πρόβλεψης")
            h_da = hd_c/h_t if h_t>0 else 0
            a_da = ad_c/a_t if a_t>0 else 0
            st.markdown(f"- 🤝 **Γηπεδούχος Draw%:** {h_da*100:.0f}%")
            st.markdown(f"- 🤝 **Φιλοξενούμενος Draw%:** {a_da*100:.0f}%")
            st.markdown(f"- 📊 **Ιστορικό Draw Factor:** {hist_factor:.2f}")
            st.markdown(f"- 📊 **Odds Trust:** {trust_level} ({(1-odds_weight)*100:.0f}% stats)")

        with col2:
            st.markdown("### ⚖️ Value Analysis")
            vm = {'home_edge':'Άσος (1)','draw_edge':'Ισοπαλία (Χ)','away_edge':'Διπλό (2)'}
            va = metrics.get('value_amount',0)
            bv = metrics.get('best_value','home_edge')
            if abs(va)>5:
                icon = "✅" if va>0 else "❌"
                lbl  = "Value bet" if va>0 else "Υπερτιμημένο"
                st.markdown(f"{icon} **{lbl}**: {va:+.1f}% στο {vm[bv]}")
            else:
                st.markdown(f"⚖️ **Δίκαιη απόδοση**: {va:+.1f}% διαφορά")

        st.markdown("---")
        st.markdown("### 📈 Σύγκριση Πιθανοτήτων")
        prob_1X=p1+pX; prob_X2=pX+p2; prob_12=p1+p2
        i1X=1/(1/odd1+1/oddX) if odd1>1.01 and oddX>1.01 else 0
        iX2=1/(1/oddX+1/odd2) if oddX>1.01 and odd2>1.01 else 0
        i12=1/(1/odd1+1/odd2) if odd1>1.01 and odd2>1.01 else 0

        comp = {
            'Σημείο':  ['1','X','2','1X','X2','12'],
            'Απόδοση': [f"{odd1:.2f}",f"{oddX:.2f}",f"{odd2:.2f}",
                        f"{i1X:.2f}" if i1X else "-",
                        f"{iX2:.2f}" if iX2 else "-",
                        f"{i12:.2f}" if i12 else "-"],
            'Μοντέλο': [f"{p1*100:.1f}%",f"{pX*100:.1f}%",f"{p2*100:.1f}%",
                        f"{prob_1X*100:.1f}%",f"{prob_X2*100:.1f}%",f"{prob_12*100:.1f}%"],
            'Bookie':  [f"{1/odd1*100:.1f}%",f"{1/oddX*100:.1f}%",f"{1/odd2*100:.1f}%",
                        f"{1/i1X*100:.1f}%" if i1X else "-",
                        f"{1/iX2*100:.1f}%" if iX2 else "-",
                        f"{1/i12*100:.1f}%" if i12 else "-"],
            'Διαφορά': [f"{p1*100-1/odd1*100:+.1f}%",
                        f"{pX*100-1/oddX*100:+.1f}%",
                        f"{p2*100-1/odd2*100:+.1f}%",
                        f"{prob_1X*100-1/i1X*100:+.1f}%" if i1X else "-",
                        f"{prob_X2*100-1/iX2*100:+.1f}%" if iX2 else "-",
                        f"{prob_12*100-1/i12*100:+.1f}%" if i12 else "-"],
        }
        st.dataframe(comp, use_container_width=True, hide_index=True)

        st.markdown("---")
        st.markdown("### 💰 Fair Odds — Τι Έπρεπε να Είναι οι Αποδόσεις")

        # Stats-only probabilities (χωρίς blend με αποδόσεις)
        sp1, spX, sp2 = stat_p1, stat_pX, stat_p2

        def fair_odd(p):
            return f"{1/p:.2f}" if p > 0.01 else "-"

        def value_icon(bookie, fair_p):
            if fair_p <= 0.01: return "—"
            v = (bookie / (1/fair_p) - 1) * 100
            if v > 20:   return f"🔥 +{v:.0f}%"
            elif v > 10: return f"✅ +{v:.0f}%"
            elif v < -10: return f"❌ {v:.0f}%"
            else:         return f"⚖️ {v:+.0f}%"

        margin = (1/odd1 + 1/oddX + 1/odd2 - 1) * 100

        fair_data = {
            'Σημείο':         ['1', 'X', '2'],
            'Bookie':         [f"{odd1:.2f}", f"{oddX:.2f}", f"{odd2:.2f}"],
            'Fair (μοντέλο)': [fair_odd(p1), fair_odd(pX), fair_odd(p2)],
            'Fair (stats)':   [fair_odd(sp1), fair_odd(spX), fair_odd(sp2)],
            'Value vs model': [value_icon(odd1,p1), value_icon(oddX,pX), value_icon(odd2,p2)],
            'Value vs stats': [value_icon(odd1,sp1), value_icon(oddX,spX), value_icon(odd2,sp2)],
        }
        st.dataframe(fair_data, use_container_width=True, hide_index=True)
        st.caption(f"Bookie margin: {margin:.1f}% | 🔥 >20% value | ✅ 10-20% value | ❌ overpriced | ⚖️ fair")

        # Value alert
        best_val = max(
            [(odd1,p1,'1'),(oddX,pX,'X'),(odd2,p2,'2')],
            key=lambda x: (x[0]/(1/x[1])-1) if x[1]>0.01 else -99
        )
        best_val_stats = max(
            [(odd1,sp1,'1'),(oddX,spX,'X'),(odd2,sp2,'2')],
            key=lambda x: (x[0]/(1/x[1])-1) if x[1]>0.01 else -99
        )
        val_pct = (best_val[0]/(1/best_val[1])-1)*100 if best_val[1]>0.01 else 0
        val_pct_s = (best_val_stats[0]/(1/best_val_stats[1])-1)*100 if best_val_stats[1]>0.01 else 0

        if val_pct_s > 20:
            st.markdown(f"""
            <div style="background:#fff3cd;border:2px solid #f39c12;border-radius:10px;
                        padding:12px;margin-top:10px;text-align:center;font-weight:bold;">
                🔥 VALUE ALERT: Το <b>{best_val_stats[2]}</b> ({best_val_stats[0]:.2f})
                έχει +{val_pct_s:.0f}% value βάσει stats!
                Fair τιμή: {fair_odd(best_val_stats[1])}
            </div>""", unsafe_allow_html=True)
        elif val_pct > 10:
            st.markdown(f"""
            <div style="background:#d4edda;border:2px solid #2ecc71;border-radius:10px;
                        padding:12px;margin-top:10px;text-align:center;font-weight:bold;">
                ✅ VALUE: Το <b>{best_val[2]}</b> ({best_val[0]:.2f})
                έχει +{val_pct:.0f}% value βάσει μοντέλου.
                Fair τιμή: {fair_odd(best_val[1])}
            </div>""", unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("### 💡 Συμβουλή Διαχείρισης Ρίσκου")
        st.info(get_risk_advice(conf, total, top_two_prob, main_point, top_two))
    else:
        st.info("ℹ️ Ανεπαρκή δεδομένα (χρειάζονται ≥6 παιχνίδια)")

st.markdown("---")

# ==============================
# BAR CHART
# ==============================
if total >= 6:
    fig = go.Figure()
    fig.add_trace(go.Bar(
        name='Bookie %', x=['1','X','2'], y=[pm1*100,pmX*100,pm2*100],
        marker_color='#1e3c72',
        text=[f"<b>{pm1*100:.1f}%</b>",f"<b>{pmX*100:.1f}%</b>",f"<b>{pm2*100:.1f}%</b>"],
        textposition='inside', textfont=dict(color="white",size=14)
    ))
    fig.add_trace(go.Bar(
        name='Model v5.4 %', x=['1','X','2'], y=[p1*100,pX*100,p2*100],
        marker_color='#2ecc71',
        text=[f"<b>{p1*100:.1f}%</b>",f"<b>{pX*100:.1f}%</b>",f"<b>{p2*100:.1f}%</b>"],
        textposition='inside', textfont=dict(color="white",size=14)
    ))
    fig.update_layout(
        barmode='group', height=350,
        xaxis=dict(type='category'),
        margin=dict(l=20,r=20,t=20,b=20),
        legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1)
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("📊 Συμπλήρωσε τουλάχιστον 6 παιχνίδια για το γράφημα")

st.markdown("---")
st.caption(
    "Soccer Match Analyzer v5.4 — "
    "Geometric Stats Model | Entropy Confidence | "
    "Graduated Trust | Smart Double Chance | Fair Odds Table"
)
