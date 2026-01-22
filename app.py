import streamlit as st
import pandas as pd

# Ρύθμιση Σελίδας
st.set_page_config(page_title="Real Stats Model v17.2.0", layout="centered")

def calculate_predictions(odds_1, odds_X, odds_2, home_stats, away_stats):
    # 1. Πιθανότητες Bookie
    total_implied = (1/odds_1) + (1/odds_X) + (1/odds_2)
    p1_book = (1/odds_1) / total_implied
    pX_book = (1/odds_X) / total_implied
    p2_book = (1/odds_2) / total_implied

    # 2. Real Stats
    h_total = sum(home_stats.values())
    a_total = sum(away_stats.values())
    
    if h_total == 0 or a_total == 0:
        return None, "⚠️ Statistics are very low, abstention is recommended."

    p1_real = home_stats['wins'] / h_total
    pX_real = (home_stats['draws'] + away_stats['draws']) / (h_total + a_total)
    p2_real = away_stats['wins'] / a_total
    
    # Alpha Calibration (0.5)
    alpha = 0.5
    p1_f = (p1_real * alpha) + (p1_book * (1 - alpha))
    pX_f = (pX_real * alpha) + (pX_book * (1 - alpha))
    p2_f = (p2_real * alpha) + (p2_book * (1 - alpha))

    norm = p1_f + pX_f + p2_f
    p1, pX, p2 = p1_f/norm, pX_f/norm, p2_f/norm

    # 3. Decision Logic
    if (p1 + p2) < 0.40:
        return None, "⚠️ HIGH RISK MATCH: Statistics are very low."

    # Προσδιορισμός Κυρίαρχου
    if p1 > pX and p1 > p2: primary = "1"
    elif p2 > p1 and p2 > pX: primary = "2"
    else: primary = "X"

    # ΕΦΑΡΜΟΓΗ ΚΑΝΟΝΑ 2.80 & ΚΑΛΥΨΗΣ 1 (1X)
    current_odds = odds_1 if primary == "1" else (odds_2 if primary == "2" else odds_X)
    
    if current_odds >= 2.80:
        if primary == "1" and (pX > 0.10 or away_stats['draws'] > 0):
            suggestion = "1 (1X)"
        elif primary == "2" and (pX > 0.10 or home_stats['draws'] > 0):
            suggestion = "2 (X2)"
        else:
            suggestion = primary
    else:
        suggestion = primary

    # Λοιποί Κανόνες (Real Stat X, κτλ)
    if pX > 0.40 and "X" not in suggestion: suggestion = f"{suggestion}X"
    
    home_pos = (home_stats['wins'] + home_stats['draws']) / h_total
    away_pos = (away_stats['wins'] + away_stats['draws']) / a_total
    if away_pos >= 2 * home_pos and home_pos > 0: suggestion = "X2"
    elif home_pos >= 2 * away_pos and away_pos > 0: suggestion = "1X"
    
    if p1 > 0.45 and p2 > 0.45: suggestion = "1-2"
    if pX < 0.15: suggestion = "1-2"

    trap = ""
    if odds_1 <= 1.50 and pX > 0.25:
        trap = "⚠️ TRAP στο Χ: Ο φαβορί θα δυσκολευτεί!"

    return {"p1": p1, "pX": pX, "p2": p2, "sug": suggestion, "conf": int(max(p1,pX,p2)*100), "trap": trap}, None

# --- STREAMLIT UI ---
st.title("⚽ Real Stats Predictor v17.2.0")

col1, col2, col3 = st.columns(3)
o1 = col1.number_input("Απόδοση 1", value=2.70)
oX = col2.number_input("Απόδοση X", value=3.40)
o2 = col3.number_input("Απόδοση 2", value=2.50)

st.divider()

c1, c2 = st.columns(2)
with c1:
    st.subheader("🏠 Γηπεδούχος")
    h_w = st.number_input("Νίκες Η", value=3, step=1)
    h_d = st.number_input("Ισοπαλίες Η", value=0, step=1)
    h_l = st.number_input("Ήττες Η", value=0, step=1)
with c2:
    st.subheader("🚀 Φιλοξενούμενος")
    a_w = st.number_input("Νίκες Α", value=1, step=1)
    a_d = st.number_input("Ισοπαλίες Α", value=1, step=1)
    a_l = st.number_input("Ήττες Α", value=1, step=1)

if st.button("Ανάλυση Αγώνα"):
    res, err = calculate_predictions(o1, oX, o2, {'wins': h_w, 'draws': h_d, 'losses': h_l}, {'wins': a_w, 'draws': a_d, 'losses': a_l})
    
    if err:
        st.error(err)
    else:
        st.metric("Πρόταση", f"{res['sug']} (VALUE)")
        st.write(f"**Confidence:** {res['conf']}%")
        if res['trap']: st.warning(res['trap'])
        
        # Γράφημα Πιθανοτήτων
        chart_data = pd.DataFrame({
            'Σημείο': ['1', 'X', '2'],
            'Πιθανότητα %': [res['p1']*100, res['pX']*100, res['p2']*100]
        })
        st.bar_chart(chart_data.set_index('Σημείο'))
