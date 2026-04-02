import streamlit as st
import pandas as pd
import json
import gspread
import random
from google.oauth2.service_account import Credentials

# --- 1. CONFIGURAZIONE E STILE ---
st.set_page_config(page_title="WC 2026 Contest", layout="wide")

# CSS per font giganti e allineamento perfetto
st.markdown("""
    <style>
    .match-card {
        background-color: #ffffff;
        border: 2px solid #e1e4e8;
        border-radius: 15px;
        padding: 15px;
        text-align: center;
        box-shadow: 0 4px 10px rgba(0,0,0,0.08);
        margin-bottom: 20px;
    }
    .team-name { font-size: 22px !important; font-weight: 900 !important; color: #1e1e1e; margin: 10px 0; }
    .pts-box { font-size: 18px !important; color: #d32f2f; background: #fff5f5; padding: 8px; border-radius: 8px; margin-top: 15px; font-weight: bold; border: 1px solid #ffc1c1; }
    .vs-text { font-size: 18px; font-weight: bold; color: #bbb; }
    .stNumberInput input { font-size: 24px !important; height: 50px !important; text-align: center !important; font-weight: bold !important; }
    h1, h2, h3 { font-size: 40px !important; font-weight: 800 !important; }
    .stTabs [data-baseweb="tab"] { font-size: 20px !important; font-weight: bold !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATABASE RANKING UFFICIALE  ---
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
    return f"https://flagcdn.com/w160/{m.get(t, 'un')}.png"

# --- 3. LOGICA CONNESSIONE ---
def connetti_gsheet():
    try:
        # Recupero sicuro dei secrets
        if "service_account" not in st.secrets:
            return "ERRORE: Secret 'service_account' mancante in Streamlit."
        
        raw_json = st.secrets["service_account"]
        info_chiave = json.loads(raw_json)
        
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(info_chiave, scopes=scope)
        client = gspread.authorize(creds)
        
        # URL DEL TUO FOGLIO
        url_foglio = "https://docs.google.com/spreadsheets/d/1palUSBw4IlBFzU4dKtgT0tnjPiPEtxIc6K-DK05vXG8/edit?gid=0#gid=0" # <--- METTI IL TUO URL VERO QUI
        return client.open_by_url(url_foglio).sheet1
    except Exception as e:
        return f"Errore tecnico: {str(e)}"

# --- 4. GENERAZIONE DATI ---
@st.cache_data
def get_tournament_structure():
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
    for g_id, teams in g.items():
        for h, a in [(0,1), (2,3), (0,2), (1,3), (0,3), (1,2)]:
            ml.append({"gr": g_id, "h": teams[h], "a": teams[a]})
    return g, ml

G_TEAMS, MATCHES = get_tournament_structure()

# --- 5. INTERFACCIA ---
st.title("🏆 FIFA World Cup 2026 Contest")
nick = st.text_input("✨ Inserisci Nickname per sbloccare:", placeholder="Es. Bomber10")

if nick:
    tab1, tab2, tab3, tab4 = st.tabs(["🌍 Gironi", "📊 Classifiche", "⚔️ Bracket", "🚀 Invia"])

    with tab1:
        if st.button("🎲 Compila Automaticamente per Test"):
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
                    pt1, pt2 = RANKING_FIFA[m['a']], RANKING_FIFA[m['h']]
                    ptx = (pt1 + pt2) // 2
                    with cols[c]:
                        st.markdown(f"""
                        <div class="match-card">
                            <div style="font-weight:bold; color:red;">GIRONE {m['gr']}</div>
                            <div style="display:flex; justify-content:space-around; align-items:center; margin-top:15px;">
                                <div style="width:40%"><img src="{get_flag(m['h'])}" width="60"><div class="team-name">{m['h']}</div></div>
                                <div class="vs-text">VS</div>
                                <div style="width:40%"><img src="{get_flag(m['a'])}" width="60"><div class="team-name">{m['a']}</div></div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        ci = st.columns(2)
                        with ci[0]: h_val = st.number_input("H", 0, 9, key=f"h_{idx}", label_visibility="collapsed")
                        with ci[1]: a_val = st.number_input("A", 0, 9, key=f"a_{idx}", label_visibility="collapsed")
                        st.markdown(f"<div class='pts-box'>1: {pt1} | X: {ptx} | 2: {pt2}</div>", unsafe_allow_html=True)

    with tab2:
        st.header("Classifiche")
        # Logica ricalcolo...
        for g_id, teams in G_TEAMS.items():
            st.write(f"**Girone {g_id}**")
            # Qui andrebbe il DataFrame della classifica come nei codici precedenti

    with tab3:
        st.header("⚔️ Compila il tuo Bracket Finale")
        st.write("Seleziona chi vince ogni scontro diretto fino alla finale!")
        
        col_b1, col_b2 = st.columns(2)
        with col_b1:
            st.subheader("Sedicesimi e Ottavi")
            s1 = st.selectbox("Sedicesimo 1", ["Squadra A", "Squadra B"], key="s1")
            s2 = st.selectbox("Sedicesimo 2", ["Squadra C", "Squadra D"], key="s2")
            ottavo1 = st.selectbox("Ottavo 1 (Vinc. S1 vs Vinc. S2)", [s1, s2], key="o1")
            
        with col_b2:
            st.subheader("Fase Finale")
            quarto = st.selectbox("Quarto di Finale", ["Vinc. Ottavo 1", "Vinc. Ottavo 2"], key="q1")
            semi = st.selectbox("Semifinale", ["Vinc. Quarto 1", "Vinc. Quarto 2"], key="semi1")
            vincitore = st.selectbox("🏆 VINCITORE MONDIALE", [semi, "Sfidante"], key="winner")
            
        if vincitore:
            st.success(f"Il tuo campione è: **{vincitore}** 🏆")

    with tab4:
        st.header("Invia Pronostici")
        if st.button("🚀 SALVA TUTTO", type="primary"):
            risultato = connetti_gsheet()
            if isinstance(risultato, str):
                st.error(risultato)
                st.info("Suggerimento: Controlla di aver incollato il JSON correttamente nei Secrets di Streamlit tra tre apici '''")
            else:
                # Salvataggio dati...
                st.success("Dati inviati con successo!")
                st.balloons()
