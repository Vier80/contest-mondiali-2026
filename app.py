import streamlit as st
import pandas as pd
import json
import gspread
import random
from google.oauth2.service_account import Credentials

# --- 1. CONFIGURAZIONE ESTETICA (CSS) ---
st.set_page_config(page_title="WC 2026 Predictor", layout="wide")

st.markdown("""
    <style>
    /* Card delle partite con altezza fissa e allineamento perfetto */
    .match-card {
        background-color: #ffffff;
        border: 2px solid #e1e4e8;
        border-radius: 15px;
        padding: 15px;
        text-align: center;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
        margin-bottom: 25px;
        height: 280px; /* Altezza bloccata per evitare disallineamenti */
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    .group-label { color: #d32f2f; font-weight: 900; font-size: 14px; margin-bottom: 10px; }
    .team-name { font-size: 18px !important; font-weight: 800 !important; color: #333; line-height: 1.1; height: 40px; display: flex; align-items: center; justify-content: center; }
    .vs-text { font-size: 16px; font-weight: bold; color: #bbb; padding-top: 10px; }
    .pts-box { font-size: 15px !important; color: #1e1e1e; background: #f8f9fa; padding: 6px; border-radius: 8px; border: 1px solid #eee; font-weight: bold; }
    
    /* Input numeri più grandi */
    .stNumberInput input { font-size: 20px !important; font-weight: bold !important; text-align: center !important; }
    
    /* Layout Admin invisibile in alto a destra */
    .admin-container { position: absolute; top: 0; right: 0; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATABASE RANKING (Dal tuo PDF) ---
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
    return f"https://flagcdn.com/w160/{m.get(t, 'un')}.png"

# --- 3. LOGICA CONNESSIONE ---
def save_data(nickname, data):
    try:
        js = json.loads(st.secrets["service_account"])
        creds = Credentials.from_service_account_info(js, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
        client = gspread.authorize(creds)
        # INCOLLA QUI IL TUO URL
        url = "https://docs.google.com/spreadsheets/d/1palUSBw4IlBFzU4dKtgT0tnjPiPEtxIc6K-DK05vXG8/edit?gid=0#gid=0"
        client.open_by_url(url).sheet1.append_row([nickname, json.dumps(data)])
        return True
    except: return False

# --- 4. STRUTTURA TORNEO ---
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
    matches = []
    for gid, teams in g.items():
        for h, a in [(0,1), (2,3), (0,2), (1,3), (0,3), (1,2)]:
            matches.append({"gr": gid, "h": teams[h], "a": teams[a]})
    return g, matches

G_TEAMS, MATCHES = get_data()

# --- 5. INTERFACCIA ---
# Barra Admin in alto a destra
col_title, col_admin = st.columns([8, 2])
with col_title: st.title("🏆 World Cup 2026 Contest")
with col_admin: 
    a_pass = st.text_input("🔑 Access", type="password", help="Area riservata")
    is_admin = (a_pass == "mondiali2026")

nick = st.text_input("👤 Nickname partecipante:", placeholder="Inserisci il tuo nome...")

if nick:
    t1, t2, t3, t4 = st.tabs(["🌍 Gironi", "📊 Classifiche", "⚔️ Bracket", "🚀 Invia"])

    with t1:
        if st.button("🎲 Compila Automaticamente"):
            for i in range(72):
                st.session_state[f"h_{i}"] = random.randint(0, 3)
                st.session_state[f"a_{i}"] = random.randint(0, 3)
            st.rerun()

        for r in range(0, 72, 4):
            cols = st.columns(4)
            for c in range(4):
                idx = r + c
                if idx < 72:
                    m = MATCHES[idx]
                    # CORREZIONE RANKING: 1 prende ranking di away, 2 prende ranking di home
                    p1, p2 = RANKING[m['a']], RANKING[m['h']]
                    px = (p1 + p2) // 2
                    with cols[c]:
                        st.markdown(f'<div class="match-card"><div class="group-label">GIRONE {m["gr"]}</div>', unsafe_allow_html=True)
                        cc1, cc2, cc3 = st.columns([1, 0.3, 1])
                        with cc1:
                            st.image(get_flag(m['h']), width=60)
                            st.markdown(f'<div class="team-name">{m["h"]}</div>', unsafe_allow_html=True)
                            h_in = st.number_input("H", 0, 9, key=f"h_{idx}", label_visibility="collapsed")
                        with cc2: st.markdown('<div class="vs-text" style="margin-top:45px;">VS</div>', unsafe_allow_html=True)
                        with cc3:
                            st.image(get_flag(m['a']), width=60)
                            st.markdown(f'<div class="team-name">{m["a"]}</div>', unsafe_allow_html=True)
                            a_in = st.number_input("A", 0, 9, key=f"a_{idx}", label_visibility="collapsed")
                        st.markdown(f'<div class="pts-box">1: {p1} | X: {px} | 2: {p2}</div></div>', unsafe_allow_html=True)

    with t2:
        st.header("Classifiche Real-Time")
        # Motore di calcolo classifiche
        cl_data = {g: {t: {"Pt":0, "DR":0, "GF":0} for t in ts} for g, ts in G_TEAMS.items()}
        for i, m in enumerate(MATCHES):
            hg, ag = st.session_state.get(f"h_{i}", 0), st.session_state.get(f"a_{i}", 0)
            sh, sa = cl_data[m['gr']][m['h']], cl_data[m['gr']][m['a']]
            sh["GF"] += hg; sa["GF"] += ag
            sh["DR"] += (hg-ag); sa["DR"] += (ag-hg)
            if hg > ag: sh["Pt"] += 3
            elif ag > hg: sa["Pt"] += 3
            else: sh["Pt"] += 1; sa["Pt"] += 1
        
        # Visualizzazione 3 per riga
        for r in range(0, 12, 3):
            cols_cl = st.columns(3)
            for k in range(3):
                gid = list(G_TEAMS.keys())[r+k]
                df = pd.DataFrame(cl_data[gid]).T.sort_values(["Pt","DR","GF"], ascending=False)
                with cols_cl[k]:
                    st.subheader(f"Gruppo {gid}")
                    st.table(df)

    with t3:
        st.header("⚔️ Bracket ad eliminazione diretta")
        # Estrazione automatica vincitori e migliori terze
        winners, runners, thirds = [], [], []
        for g, ts in cl_data.items():
            sort = pd.DataFrame(ts).T.sort_values(["Pt","DR","GF"], ascending=False)
            winners.append(sort.index[0]); runners.append(sort.index[1]); thirds.append({"t": sort.index[2], "p": sort.iloc[2]["Pt"], "dr": sort.iloc[2]["DR"], "gf": sort.iloc[2]["GF"], "g": g})
        
        # Top 8 Terze
        best_3 = pd.DataFrame(thirds).sort_values(["p","dr","gf"], ascending=False).head(8)["t"].tolist()
        
        st.subheader("Accoppiamenti Sedicesimi")
        # Esempio primi match da matrice
        c_b1, c_b2 = st.columns(2)
        with c_b1:
            st.info(f"Match 1: (2A) {runners[0]} vs (2C) {runners[2]}")
            m1 = st.selectbox("Vincitore Match 1", [runners[0], runners[2]], key="m1")
            st.info(f"Match 2: (1D) {winners[3]} vs (3°) {best_3[0] if len(best_3)>0 else '...'}")
            m2 = st.selectbox("Vincitore Match 2", [winners[3], best_3[0]], key="m2")
        with c_b2:
            st.success(f"Quarto 1: {m1} vs {m2}")
            finalist = st.selectbox("VINCITORE FINALE 🏆", [m1, m2, "Sfidante..."], key="f")

    with t4:
        if st.button("🚀 INVIA PRONOSTICI DEFINITIVI", type="primary"):
            if save_data(nick, cl_data):
                st.balloons(); st.success("Salvataggio completato!")

if is_admin:
    st.divider(); st.subheader("⚙️ Controllo Admin"); st.write("Qui caricherai i risultati reali.")
