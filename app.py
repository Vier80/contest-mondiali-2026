import streamlit as st
import pandas as pd
import json
import gspread
import random
from google.oauth2.service_account import Credentials

# --- 1. CONFIGURAZIONE E CSS ---
st.set_page_config(page_title="WC 2026 PRO", layout="wide")

st.markdown("""
    <style>
    .match-card { background-color: #fff; border: 2px solid #f0f2f6; border-radius: 12px; padding: 12px; text-align: center; height: 260px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    .team-name { font-size: 18px !important; font-weight: 800; height: 45px; display: flex; align-items: center; justify-content: center; }
    .pts-label { font-size: 16px !important; color: #d32f2f; font-weight: bold; background: #fff1f1; padding: 4px; border-radius: 5px; margin-top: 10px; }
    .stNumberInput input { font-size: 20px !important; font-weight: bold !important; text-align: center !important; }
    .bracket-match { background: #f8f9fa; border-left: 5px solid #007bff; padding: 10px; border-radius: 5px; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. RANKING E DATI ---
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

def get_flag(t):
    m = {"Messico": "mx", "Sudafrica": "za", "Sudcorea": "kr", "Repubblica Ceca": "cz", "Canada": "ca", "Bosnia Erzegovina": "ba", "Qatar": "qa", "Svizzera": "ch", "Brasile": "br", "Marocco": "ma", "Haiti": "ht", "Scozia": "gb-sct", "USA": "us", "Paraguay": "py", "Australia": "au", "Turchia": "tr", "Germania": "de", "Curacao": "cw", "Costa D'Avorio": "ci", "Ecuador": "ec", "Olanda": "nl", "Giappone": "jp", "Svezia": "se", "Tunisia": "tn", "Belgio": "be", "Egitto": "eg", "Iran": "ir", "Nuova Zelanda": "nz", "Spagna": "es", "Capo Verde": "cv", "Arabia Saudita": "sa", "Uruguay": "uy", "Francia": "fr", "Senegal": "sn", "Iraq": "iq", "Norvegia": "no", "Argentina": "ar", "Algeria": "dz", "Austria": "at", "Giordania": "jo", "Portogallo": "pt", "DR Congo": "cd", "Uzbekistan": "uz", "Colombia": "co", "Inghilterra": "gb-eng", "Croazia": "hr", "Ghana": "gh", "Panama": "pa", "Italia": "it"}
    return f"https://flagcdn.com/w80/{m.get(t, 'un')}.png"

@st.cache_data
def load_structure():
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
        for h, a in [(0,1), (2,3), (0,2), (1,3), (0,3), (1,2)]:
            ml.append({"gr": gid, "h": teams[h], "a": teams[a]})
    return g, ml

G_TEAMS, MATCHES = load_structure()

# --- 3. LOGICA CONNESSIONE ---
def save_to_db(nickname, data):
    try:
        js = json.loads(st.secrets["service_account"])
        creds = Credentials.from_service_account_info(js, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
        client = gspread.authorize(creds)
        # INCOLLA QUI IL TUO URL
        sheet = client.open_by_url("https://docs.google.com/spreadsheets/d/1palUSBw4IlBFzU4dKtgT0tnjPiPEtxIc6K-DK05vXG8/edit?gid=0#gid=0").sheet1
        sheet.append_row([nickname, json.dumps(data)])
        return True
    except Exception as e:
        st.error(f"Errore DB: {e}")
        return False

# --- 4. INTERFACCIA ---
c1, c2 = st.columns([7, 3])
with c1: st.title("🏆 WC 2026 Predictor")
with c2: 
    adm = st.text_input("Admin Access", type="password")
    is_admin = (adm == "mondiali2026")

nick = st.text_input("👤 Inserisci il tuo Nickname per giocare:", key="nick")

if nick:
    tab1, tab2, tab3, tab4 = st.tabs(["🌎 Gironi", "📊 Classifiche", "⚔️ Bracket", "🚀 Invia"])

    with tab1:
        if st.button("🎲 Compila Automaticamente (TEST)"):
            for i in range(72):
                st.session_state[f"h_{i}"] = random.randint(0,3)
                st.session_state[f"a_{i}"] = random.randint(0,3)
            st.rerun()

        for r in range(0, 72, 4):
            cols = st.columns(4)
            for c in range(4):
                idx = r + c
                if idx < 72:
                    m = MATCHES[idx]
                    p1, p2 = RANKING[m['a']], RANKING[m['h']]
                    px = (p1 + p2) // 2
                    with cols[c]:
                        st.markdown(f'<div class="match-card"><b style="color:#007bff;">GIRONE {m["gr"]}</b>', unsafe_allow_html=True)
                        mc1, mc2, mc3 = st.columns([1, 0.4, 1])
                        with mc1:
                            st.image(get_flag(m['h']), width=50)
                            st.markdown(f'<div class="team-name">{m["h"]}</div>', unsafe_allow_html=True)
                            h_in = st.number_input("H", 0, 9, key=f"h_{idx}", label_visibility="collapsed")
                        with mc2: st.markdown('<div style="margin-top:40px; font-weight:bold;">VS</div>', unsafe_allow_html=True)
                        with mc3:
                            st.image(get_flag(m['a']), width=50)
                            st.markdown(f'<div class="team-name">{m["a"]}</div>', unsafe_allow_html=True)
                            a_in = st.number_input("A", 0, 9, key=f"a_{idx}", label_visibility="collapsed")
                        st.markdown(f'<div class="pts-label">1: {p1} | X: {px} | 2: {p2}</div></div>', unsafe_allow_html=True)

    with tab2:
        st.header("Classifiche Gironi")
        stats = {g: {t: {"Pt":0, "DR":0, "GF":0} for t in ts} for g, ts in G_TEAMS.items()}
        for i, m in enumerate(MATCHES):
            hg, ag = st.session_state.get(f"h_{i}", 0), st.session_state.get(f"a_{i}", 0)
            sh, sa = stats[m['gr']][m['h']], stats[m['gr']][m['a']]
            sh["GF"] += hg; sa["GF"] += ag
            sh["DR"] += (hg-ag); sa["DR"] += (ag-hg)
            if hg > ag: sh["Pt"] += 3
            elif ag > hg: sa["Pt"] += 3
            else: sh["Pt"] += 1; sa["Pt"] += 1

        final_standings = {}
        for r in range(0, 12, 3):
            cr = st.columns(3)
            for k in range(3):
                gid = list(G_TEAMS.keys())[r+k]
                df = pd.DataFrame(stats[gid]).T.sort_values(["Pt","DR","GF"], ascending=False)
                final_standings[gid] = df.index.tolist()
                with cr[k]:
                    st.subheader(f"Gruppo {gid}")
                    st.table(df)

    with tab3:
        st.header("⚔️ Bracket Automata")
        # Estrazione terze
        thirds = []
        for gid, ts in stats.items():
            sorted_t = pd.DataFrame(ts).T.sort_values(["Pt","DR","GF"], ascending=False)
            thirds.append({"team": sorted_t.index[2], "Pt": sorted_t.iloc[2]["Pt"], "DR": sorted_t.iloc[2]["DR"], "GF": sorted_t.iloc[2]["GF"], "gr": gid})
        
        best_thirds_df = pd.DataFrame(thirds).sort_values(["Pt","DR","GF"], ascending=False).head(8)
        bt_list = best_thirds_df["team"].tolist()
        bt_gr = set(best_thirds_df["gr"].tolist())

        st.subheader("Accoppiamenti Sedicesimi (In base alla tua Matrice)")
        # Esempio logica sedicesimi
        s1 = [final_standings["A"][1], final_standings["C"][1]]
        s2 = [final_standings["D"][0], bt_list[0] if len(bt_list)>0 else "3° D/E/F"]
        
        c_b1, c_b2 = st.columns(2)
        with c_b1:
            st.markdown(f'<div class="bracket-match"><b>Match 1:</b> {s1[0]} vs {s1[1]}</div>', unsafe_allow_html=True)
            v1 = st.selectbox("Chi vince Match 1?", s1, key="v1")
            st.markdown(f'<div class="bracket-match"><b>Match 2:</b> {s2[0]} vs {s2[1]}</div>', unsafe_allow_html=True)
            v2 = st.selectbox("Chi vince Match 2?", s2, key="v2")
        
        with c_b2:
            st.markdown(f'<div class="bracket-match"><b>QUARTO 1:</b> {v1} vs {v2}</div>', unsafe_allow_html=True)
            winner = st.selectbox("VINCITORE FINALE", [v1, v2, "Sfidante..."], key="fin")

    with tab4:
        if st.button("🚀 INVIA PRONOSTICI", type="primary"):
            if save_to_db(nick, stats):
                st.balloons()
                st.success("Tutto inviato correttamente!")

if is_admin:
    st.divider()
    st.subheader("⚙️ Area Amministratore")
    st.write("Dati grezzi e gestione database.")
