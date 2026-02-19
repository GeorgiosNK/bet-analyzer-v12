# ==============================
# CALCULATIONS ENGINE (ΔΙΟΡΘΩΜΕΝΟ)
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
