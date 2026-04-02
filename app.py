import streamlit as st
import pandas as pd
import json
import gspread
import random
from google.oauth2.service_account import Credentials

# --- 1. CONFIGURAZIONE PAGINA E STILE ---
st.set_page_config(page_title="WC 2026 Contest", layout="wide")

st.markdown("""
    <style>
    .match-card {
        background-color: #ffffff;
        border: 1px solid #e1e4e8;
        border-radius: 12px;
        padding: 10px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        margin-bottom: 15px;
        min-height: 160px;
    }
    .team-name { font-size: 14px !important; font-weight: bold; margin-top: 5px; min-height: 40px; display: flex; align-items: center; justify-content: center; }
    .pts-box { font-size: 11px; color: #555; background: #f1f3f5; padding: 4px; border-radius: 6px; margin-top: 10px; font-weight: bold; }
    .stNumberInput input { text-align: center; font-weight: bold; font-size: 18px !important; }
    div[data-testid="column"] { padding: 0 5px !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CONNESSIONE GOOGLE SHEETS ---
def connetti_gsheet():
    try:
        info_chiave = json.loads(st.secrets["service_account"])
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(info_chiave, scopes=scope)
        client = gspread.authorize(creds)
        # INCOLLA IL TUO URL QUI SOTTO
        url_foglio = "https://docs.google.com/spreadsheets/d/1palUSBw4IlBFzU4dKtgT0tnjPiPEtxIc6K-DK05vXG8/edit?gid=0#gid=0"
        return client.open_by_url(url_foglio).sheet1
    except Exception as e:
        st.error(f"Errore connessione DB: {e}")
        return None

# --- 3. DATABASE RANKING E BANDIERE ---
RANKING_FIFA = {
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

# --- 4. GENERAZIONE CALENDARIO ---
@st.cache_data
def get_matches():
    gironi = {
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
    for g, teams in gironi.items():
        pairs = [(0,1), (2,3), (0,2), (1,3), (0,3), (1,2)]
        for h, a in pairs:
            ml.append({"gr": g, "home": teams[h], "away": teams[a]})
    return gironi, ml

G_TEAMS, MATCHES = get_matches()

# --- 5. LOGICA APPLICATIVA ---
if 'results' not in st.session_state: st.session_state.results = {}

# Sidebar Admin (Discreta)
with st.sidebar:
    st.write("---")
    adm_pass = st.text_input("Access", type="password", help="Area riservata")
    is_admin = (adm_pass == "mondiali2026")

# UI Principale
st.title("🏆 FIFA World Cup 2026 Contest")
nick = st.text_input("✨ Inserisci Nickname per sbloccare il gioco:", placeholder="Esempio: Marco88")

if nick:
    tab1, tab2, tab3, tab4 = st.tabs(["🌍 Gironi", "📊 Classifiche", "⚔️ Bracket", "🚀 Invia"])

    with tab1:
        if st.button("🎲 Compila Automaticamente (TEST)"):
            for i in range(72):
                st.session_state[f"h_{i}"] = random.randint(0, 3)
                st.session_state[f"a_{i}"] = random.randint(0, 3)
            st.rerun()

        # Griglia 4x18
        for r in range(0, 72, 4):
            cols = st.columns(4)
            for c in range(4):
                idx = r + c
                if idx < 72:
                    m = MATCHES[idx]
                    pts_1 = RANKING_FIFA[m['away']]
                    pts_2 = RANKING_FIFA[m['home']]
                    pts_x = (pts_1 + pts_2) // 2
                    
                    with cols[c]:
                        st.markdown(f"""
                        <div class="match-card">
                            <div style="font-size:10px; color:#999; font-weight:bold;">GIRONE {m['gr']}</div>
                            <div style="display:flex; justify-content:space-around; align-items:flex-start; margin-top:10px;">
                                <div style="width:40%"><img src="{get_flag(m['home'])}" width="35"><div class="team-name">{m['home']}</div></div>
                                <div style="width:20%; padding-top:10px; font-weight:bold; color:#ddd;">VS</div>
                                <div style="width:40%"><img src="{get_flag(m['away'])}" width="35"><div class="team-name">{m['away']}</div></div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        ci = st.columns(2)
                        with ci[0]: h_res = st.number_input("H", 0, 9, key=f"h_{idx}", label_visibility="collapsed")
                        with ci[1]: a_res = st.number_input("A", 0, 9, key=f"a_{idx}", label_visibility="collapsed")
                        st.markdown(f"<div class='pts-box'>1: {pts_1} | X: {pts_x} | 2: {pts_2}</div>", unsafe_allow_html=True)
                        st.session_state.results[f"{m['home']}-{m['away']}"] = (h_res, a_res)

    with tab2:
        st.header("Situazione Gironi")
        standings = {g: {t: {"Pt": 0, "DR": 0, "GF": 0} for t in teams} for g, teams in G_TEAMS.items()}
        for i, m in enumerate(MATCHES):
            h_g, a_g = st.session_state.get(f"h_{i}", 0), st.session_state.get(f"a_{i}", 0)
            s_h, s_a = standings[m['gr']][m['home']], standings[m['gr']][m['away']]
            s_h["GF"] += h_g; s_a["GF"] += a_g
            s_h["DR"] += (h_g - a_g); s_a["DR"] += (a_g - h_g)
            if h_g > a_g: s_h["Pt"] += 3
            elif a_g > h_g: s_a["Pt"] += 3
            else: s_h["Pt"] += 1; s_a["Pt"] += 1

        for r in range(0, 12, 3):
            cols_g = st.columns(3)
            for k in range(3):
                g_id = list(G_TEAMS.keys())[r+k]
                df = pd.DataFrame(standings[g_id]).T.sort_values(["Pt","DR","GF"], ascending=False)
                with cols_g[k]:
                    st.subheader(f"Girone {g_id}")
                    st.dataframe(df, use_container_width=True)

    with tab3:
        st.header("Fase Finale")
        if st.button("🔥 Calcola Accoppiamenti Sedicesimi"):
            st.balloons()
            st.success("Tabellone generato! Verranno mostrate le sfide basate sui risultati dei gironi.")

    with tab4:
        st.header("Salvataggio")
        if st.button("🚀 INVIA PRONOSTICI", type="primary"):
            f = connetti_gsheet()
            if f:
                f.append_row([nick, json.dumps(st.session_state.results)])
                st.success("Dati inviati correttamente!")
            else: st.error("Errore di connessione al database.")

if is_admin:
    st.divider()
    st.subheader("🛠 Area Amministratore")
    st.write("Benvenuto nel pannello segreto.")
