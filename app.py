import streamlit as st
import pandas as pd
import json
import gspread
import random
from google.oauth2.service_account import Credentials

# --- 1. CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="WC 2026 Contest PRO", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #f8f9fa; }
    [data-testid="stMetricValue"] { font-size: 24px !important; }
    .stNumberInput input { font-size: 20px !important; font-weight: bold !important; text-align: center !important; }
    .match-card { background: white; border-radius: 10px; padding: 15px; border: 1px solid #e0e0e0; box-shadow: 2px 2px 10px rgba(0,0,0,0.05); }
    .ranking-box { background: #fff5f5; border: 1px solid #ffc1c1; color: #d32f2f; border-radius: 5px; font-size: 11px; font-weight: bold; text-align: center; margin: 10px 0; padding: 5px; }
    .team-label { font-size: 12px; font-weight: 800; text-align: center; }
</style>
""", unsafe_allow_html=True)

# --- 2. DATABASE RANKING E GRUPPI ---
RANKING = {
    "Messico": 15, "Sudafrica": 61, "Sudcorea": 22, "Repubblica Ceca": 44,
    "Canada": 27, "Bosnia Erzegovina": 71, "Qatar": 58, "Svizzera": 17,
    "Brasile": 5, "Marocco": 11, "Haiti": 84, "Scozia": 36,
    "USA": 14, "Paraguay": 39, "Australia": 26, "Turchia": 25,
    "Germania": 9, "Curacao": 82, "Costa D'Avorio": 42, "Ecuador": 23,
    "Olanda": 7, "Giappone": 18, "Svezia": 43, "Tunisia": 40,
    "Belgio": 8, "Egitto": 34, "Iran": 20, "Nuova Zelanda": 86,
    "Spagna": 1, "Capo Verde": 68, "Arabia Saudita": 60, "Uruguay": 16,
    "Francia": 3, "Senegal": 19, "Iraq": 58, "Norvegia": 29,
    "Argentina": 2, "Algeria": 35, "Austria": 24, "Giordania": 66,
    "Portogallo": 6, "DR Congo": 56, "Uzbekistan": 50, "Colombia": 13,
    "Inghilterra": 4, "Croazia": 10, "Ghana": 72, "Panama": 30, "Italia": 13
}

@st.cache_data
def get_data():
    g = {
        "A": ["Messico", "Sudafrica", "Sudcorea", "Repubblica Ceca"],
        "B": ["Canada", "Bosnia Erzegovina", "Qatar", "Svizzera"],
        "C": ["Brasile", "Marocco", "Haiti", "Scozia"],
        "D": ["USA", "Paraguay", "Australia", "Turchia"],
        "E": ["Germania", "Curacao", "Costa D'Avorio", "Ecuador"],
        "F": ["Olanda", "Giappone", "Svezia", "Tunisia"],
        "G": ["Belgio", "Egitto", "Iran", "Nuova Zelanda"],
        "H": ["Spagna", "Capo Verde", "Arabia Saudita", "Uruguay"],
        "I": ["Francia", "Senegal", "Iraq", "Norvegia"],
        "J": ["Argentina", "Algeria", "Austria", "Giordania"],
        "K": ["Portogallo", "DR Congo", "Uzbekistan", "Colombia"],
        "L": ["Inghilterra", "Croazia", "Ghana", "Panama"]
    }
    ml = []
    for gid, teams in g.items():
        pairs = [(0, 1), (2, 3), (0, 2), (1, 3), (0, 3), (1, 2)]
        for h, a in pairs:
            ml.append({"gr": gid, "h": teams[h], "a": teams[a]})
    return g, ml

G_TEAMS, MATCHES = get_data()

def get_flag(t):
    m = {
        "Messico": "mx", "Sudafrica": "za", "Sudcorea": "kr", "Repubblica Ceca": "cz",
        "Canada": "ca", "Bosnia Erzegovina": "ba", "Qatar": "qa", "Svizzera": "ch",
        "Brasile": "br", "Marocco": "ma", "Haiti": "ht", "Scozia": "gb-sct",
        "USA": "us", "Paraguay": "py", "Australia": "au", "Turchia": "tr",
        "Germania": "de", "Curacao": "cw", "Costa D'Avorio": "ci", "Ecuador": "ec",
        "Olanda": "nl", "Giappone": "jp", "Svezia": "se", "Tunisia": "tn",
        "Belgio": "be", "Egitto": "eg", "Iran": "ir", "Nuova Zelanda": "nz",
        "Spagna": "es", "Capo Verde": "cv", "Arabia Saudita": "sa", "Uruguay": "uy",
        "Francia": "fr", "Senegal": "sn", "Iraq": "iq", "Norvegia": "no",
        "Argentina": "ar", "Algeria": "dz", "Austria": "at", "Giordania": "jo",
        "Portogallo": "pt", "DR Congo": "cd", "Uzbekistan": "uz", "Colombia": "co",
        "Inghilterra": "gb-eng", "Croazia": "hr", "Ghana": "gh", "Panama": "pa", "Italia": "it"
    }
    return f"https://flagcdn.com/w160/{m.get(t, 'un')}.png"

# --- 3. LOGICA CLASSIFICHE E TERZE ---
def calcola_tutto():
    stats = {g: {t: {"Pt": 0, "DR": 0, "GF": 0} for t in ts} for g, ts in G_TEAMS.items()}
    for i, m in enumerate(MATCHES):
        h_g = st.session_state.get(f"h_{i}", 0)
        a_g = st.session_state.get(f"a_{i}", 0)
        sh, sa = stats[m['gr']][m['h']], stats[m['gr']][m['a']]
        sh["GF"] += h_g; sa["GF"] += a_g
        sh["DR"] += (h_g - a_g); sa["DR"] += (a_g - h_g)
        if h_g > a_g: sh["Pt"] += 3
        elif a_g > h_g: sa["Pt"] += 3
        else: sh["Pt"] += 1; sa["Pt"] += 1
    
    final_ranks = {}
    thirds = []
    for gid, teams_stat in stats.items():
        df_g = pd.DataFrame(teams_stat).T.sort_values(["Pt", "DR", "GF"], ascending=False)
        final_ranks[gid] = df_g.index.tolist()
        thirds.append({"team": df_g.index[2], "Pt": df_g.iloc[2]["Pt"], "DR": df_g.iloc[2]["DR"], "GF": df_g.iloc[2]["GF"], "gr": gid})
    
    best_thirds = pd.DataFrame(thirds).sort_values(["Pt", "DR", "GF"], ascending=False).head(8)
    return final_ranks, best_thirds, stats

def get_3rd(slot, b_thirds_dict):
    disponibili = sorted(b_thirds_dict.keys())
    mapping = {"1D": 0, "1B": 1, "1A": 2, "1C": 3, "1G": 4, "1I": 5, "1K": 6, "1L": 7}
    idx = mapping.get(slot, 0)
    gr_rif = disponibili[idx] if idx < len(disponibili) else disponibili[-1]
    return b_thirds_dict.get(gr_rif, "Squadra")

# --- 4. FUNZIONE SALVATAGGIO ---
def salva_pronostici(nick, dati):
    try:
        js = json.loads(st.secrets["service_account"])
        creds = Credentials.from_service_account_info(js, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
        client = gspread.authorize(creds)
        URL_FOGLIO = "https://docs.google.com/spreadsheets/d/1palUSBw4IlBFzU4dKtgT0tnjPiPEtxIc6K-DK05vXG8/edit?gid=0#gid=0" # <--- INCOLLA QUI IL TUO LINK
        sheet = client.open_by_url(URL_FOGLIO).sheet1
        sheet.append_row([nick, json.dumps(dati)])
        return True
    except: return False

# --- 5. INTERFACCIA ---
st.title("🏆 WC 2026 Contest PRO")
nick = st.text_input("👤 Nickname:", placeholder="Inserisci il tuo nome...")

if nick:
    tab1, tab2, tab3, tab4 = st.tabs(["🌍 Gironi", "📊 Classifiche", "⚔️ Bracket", "🚀 Invia"])

    with tab1:
        if st.button("🪄 Compila Random"):
            for i in range(72):
                st.session_state[f"h_{i}"] = random.randint(0, 3)
                st.session_state[f"a_{i}"] = random.randint(0, 3)
            st.rerun()

        for row in range(18):
            cols = st.columns(4)
            for c_idx in range(4):
                idx = row * 4 + c_idx
                if idx < 72:
                    m = MATCHES[idx]
                    p1, p2, px = RANKING[m['a']], RANKING[m['h']], (RANKING[m['a']] + RANKING[m['h']]) // 2
                    with cols[c_idx]:
                        with st.container(border=True):
                            st.markdown(f"<p style='text-align:center; color:red; font-size:10px; font-weight:bold;'>GIRONE {m['gr']}</p>", unsafe_allow_html=True)
                            c_f1, c_vs, c_f2 = st.columns([2,1,2])
                            c_f1.image(get_flag(m['h']), width=40)
                            c_f2.image(get_flag(m['a']), width=40)
                            st.markdown(f"<div class='ranking-box'>1: {p1} | X: {px} | 2: {p2}</div>", unsafe_allow_html=True)
                            i1, i2 = st.columns(2)
                            st.session_state[f"h_{idx}"] = i1.number_input(m['h'][:10], 0, 9, key=f"h_{idx}", value=st.session_state.get(f"h_{idx}", 0))
                            st.session_state[f"a_{idx}"] = i2.number_input(m['a'][:10], 0, 9, key=f"a_{idx}", value=st.session_state.get(f"a_{idx}", 0))

    with tab2:
        ranks, b_thirds, stats = calcola_tutto()
        for i in range(0, 12, 3):
            cols = st.columns(3)
            for k in range(3):
                gid = list(G_TEAMS.keys())[i+k]
                df = pd.DataFrame(stats[gid]).T.sort_values(["Pt", "DR", "GF"], ascending=False)
                cols[k].subheader(f"Gruppo {gid}")
                cols[k].dataframe(df, use_container_width=True)

    with tab3:
        ranks, b_thirds_df, _ = calcola_tutto()
        b_thirds = {row['gr']: row['team'] for _, row in b_thirds_df.iterrows()}
        
        # --- SEDICESIMI ---
        st.header("1️⃣ Sedicesimi di Finale")
        s_matches = [
            ("S1", ranks["A"][1], ranks["C"][1]), ("S2", ranks["D"][0], get_3rd("1D", b_thirds)),
            ("S3", ranks["B"][0], get_3rd("1B", b_thirds)), ("S4", ranks["F"][0], ranks["E"][1]),
            ("S5", ranks["B"][1], ranks["F"][1]), ("S6", ranks["A"][0], get_3rd("1A", b_thirds)),
            ("S7", ranks["E"][0], ranks["D"][1]), ("S8", ranks["C"][0], get_3rd("1C", b_thirds)),
            ("S9", ranks["G"][0], ranks["I"][1]), ("S10", ranks["H"][0], ranks["J"][1]),
            ("S11", ranks["I"][0], get_3rd("1I", b_thirds)), ("S12", ranks["J"][0], ranks["L"][1]),
            ("S13", ranks["K"][0], get_3rd("1K", b_thirds)), ("S14", ranks["L"][0], ranks["G"][1]),
            ("S15", ranks["G"][1], ranks["H"][1]), ("S16", ranks["K"][1], get_3rd("1L", b_thirds))
        ]
        
        v_s = {}
        cols_s = st.columns(4)
        for i, (m_id, t1, t2) in enumerate(s_matches):
            with cols_s[i//4]:
                with st.container(border=True):
                    st.image([get_flag(t1), get_flag(t2)], width=30)
                    v_s[m_id] = st.radio(f"Match {i+1}", [t1, t2], key=f"v_{m_id}")

        # --- OTTAVI ---
        st.header("2️⃣ Ottavi di Finale")
        o_pairs = [("S1","S2"), ("S3","S4"), ("S5","S6"), ("S7","S8"), ("S9","S10"), ("S11","S12"), ("S13","S14"), ("S15","S16")]
        v_o = {}
        cols_o = st.columns(4)
        for i, (m1, m2) in enumerate(o_pairs):
            with cols_o[i//2]:
                with st.container(border=True):
                    t1, t2 = v_s[m1], v_s[m2]
                    st.image([get_flag(t1), get_flag(t2)], width=30)
                    v_o[f"O{i}"] = st.radio(f"Ottavo {i+1}", [t1, t2], key=f"vo_{i}")

        # --- QUARTI ---
        st.header("3️⃣ Quarti di Finale")
        q_pairs = [("O0","O1"), ("O2","O3"), ("O4","O5"), ("O6","O7")]
        v_q = {}
        cols_q = st.columns(4)
        for i, (m1, m2) in enumerate(q_pairs):
            with cols_q[i]:
                with st.container(border=True):
                    t1, t2 = v_o[m1], v_o[m2]
                    st.image([get_flag(t1), get_flag(t2)], width=30)
                    v_q[f"Q{i}"] = st.radio(f"Quarto {i+1}", [t1, t2], key=f"vq_{i}")

        # --- SEMI E FINALE ---
        st.header("4️⃣ Semifinali e Finale")
        c1, c2 = st.columns(2)
        v_semi1 = c1.radio("Semi 1", [v_q["Q0"], v_q["Q1"]], key="vs1")
        v_semi2 = c2.radio("Semi 2", [v_q["Q2"], v_q["Q3"]], key="vs2")
        
        st.divider()
        campione = st.selectbox("🏆 CAMPIONE DEL MONDO:", [v_semi1, v_semi2])
        st.session_state["vincitore"] = campione
        if campione: st.balloons()

    with tab4:
        st.header("🚀 Invia Pronostici")
        if st.button("SALVA DEFINITIVAMENTE"):
            dati = {"gironi": {i: st.session_state.get(f"h_{i}") for i in range(72)}, "vincitore": st.session_state.get("vincitore")}
            if salva_pronostici(nick, dati): st.success("Inviato!")
            else: st.error("Errore invio.")
