import streamlit as st
import pandas as pd
import json
import gspread
import random
from google.oauth2.service_account import Credentials

# --- 1. CONFIGURAZIONE E STILE AVANZATO ---
st.set_page_config(page_title="WC 2026 Contest", layout="wide")

st.markdown("""
    <style>
    /* Card allineate con altezza fissa */
    .match-card {
        background-color: #ffffff;
        border: 2px solid #f0f2f6;
        border-radius: 15px;
        padding: 15px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        margin-bottom: 20px;
        height: 250px; /* Altezza fissa per allineamento totale */
    }
    .team-name { font-size: 20px !important; font-weight: 800 !important; height: 50px; display: flex; align-items: center; justify-content: center; line-height: 1.2; }
    .pts-label { font-size: 18px !important; color: #d32f2f; font-weight: bold; background: #fff5f5; padding: 5px; border-radius: 5px; display: block; margin-top: 10px; }
    .vs-text { font-size: 16px; font-weight: bold; color: #ccc; margin: 0 10px; }
    /* Font grandi per input */
    .stNumberInput input { font-size: 22px !important; font-weight: bold !important; text-align: center !important; }
    /* Posizionamento Admin in alto a destra */
    .admin-box { position: absolute; top: 0; right: 0; width: 150px; z-index: 1000; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATI RANKING UFFICIALI (Dal tuo PDF) ---
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
} # [cite: 2]

def get_flag(t):
    m = {"Messico": "mx", "Sudafrica": "za", "Sudcorea": "kr", "Repubblica Ceca": "cz", "Canada": "ca", "Bosnia Erzegovina": "ba", "Qatar": "qa", "Svizzera": "ch", "Brasile": "br", "Marocco": "ma", "Haiti": "ht", "Scozia": "gb-sct", "USA": "us", "Paraguay": "py", "Australia": "au", "Turchia": "tr", "Germania": "de", "Curacao": "cw", "Costa D'Avorio": "ci", "Ecuador": "ec", "Olanda": "nl", "Giappone": "jp", "Svezia": "se", "Tunisia": "tn", "Belgio": "be", "Egitto": "eg", "Iran": "ir", "Nuova Zelanda": "nz", "Spagna": "es", "Capo Verde": "cv", "Arabia Saudita": "sa", "Uruguay": "uy", "Francia": "fr", "Senegal": "sn", "Iraq": "iq", "Norvegia": "no", "Argentina": "ar", "Algeria": "dz", "Austria": "at", "Giordania": "jo", "Portogallo": "pt", "DR Congo": "cd", "Uzbekistan": "uz", "Colombia": "co", "Inghilterra": "gb-eng", "Croazia": "hr", "Ghana": "gh", "Panama": "pa", "Italia": "it"}
    return f"https://flagcdn.com/w160/{m.get(t, 'un')}.png"

# --- 3. CONNESSIONE SICURA ---
def connetti():
    try:
        # Recupero robot
        js = json.loads(st.secrets["service_account"])
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(js, scopes=scope)
        client = gspread.authorize(creds)
        # USA IL TUO URL QUI
        return client.open_by_url("https://docs.google.com/spreadsheets/d/1palUSBw4IlBFzU4dKtgT0tnjPiPEtxIc6K-DK05vXG8/edit?gid=0#gid=0").sheet1
    except:
        return None

# --- 4. STRUTTURA TORNEO ---
@st.cache_data
def init_data():
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
    } # [cite: 2]
    ml = []
    for gid, teams in g.items():
        for h, a in [(0,1), (2,3), (0,2), (1,3), (0,3), (1,2)]:
            ml.append({"gr": gid, "h": teams[h], "a": teams[a]})
    return g, ml

G_TEAMS, MATCHES = init_data()

# --- 5. LOGICA APP ---
# Header con Admin a destra
c_head1, c_head2 = st.columns([8, 2])
with c_head1:
    st.title("🏆 World Cup 2026 Contest")
with c_head2:
    apass = st.text_input("🔑 Admin", type="password")
    is_admin = (apass == "mondiali2026")

nick = st.text_input("👤 Nickname:", placeholder="Inserisci il tuo nome...")

if nick:
    t1, t2, t3, t4 = st.tabs(["🌎 Gironi", "📊 Classifiche", "⚔️ Bracket", "🚀 Invia"])

    with t1:
        if st.button("🎲 Compila Tutto (Test)"):
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
                        st.markdown(f'<div class="match-card"><p style="color:red; font-weight:bold;">GIRONE {m["gr"]}</p>', unsafe_allow_html=True)
                        cc1, cc2, cc3 = st.columns([1, 0.5, 1])
                        with cc1:
                            st.image(get_flag(m['h']), width=60)
                            st.markdown(f'<div class="team-name">{m["h"]}</div>', unsafe_allow_html=True)
                            h_in = st.number_input("H", 0, 9, key=f"h_{idx}", label_visibility="collapsed")
                        with cc2:
                            st.markdown('<div style="margin-top:50px;" class="vs-text">VS</div>', unsafe_allow_html=True)
                        with cc3:
                            st.image(get_flag(m['a']), width=60)
                            st.markdown(f'<div class="team-name">{m["a"]}</div>', unsafe_allow_html=True)
                            a_in = st.number_input("A", 0, 9, key=f"a_{idx}", label_visibility="collapsed")
                        st.markdown(f'<span class="pts-label">1: {p1} | X: {px} | 2: {p2}</span></div>', unsafe_allow_html=True)

    with t2:
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

        for r in range(0, 12, 3):
            cr = st.columns(3)
            for k in range(3):
                gid = list(G_TEAMS.keys())[r+k]
                df = pd.DataFrame(stats[gid]).T.sort_values(["Pt","DR","GF"], ascending=False)
                with cr[k]:
                    st.subheader(f"Gruppo {gid}")
                    st.table(df)

    with t3:
        st.header("⚔️ Fase Finale")
        st.write("Scegli i vincitori per avanzare nel tabellone")
        c_b1, c_b2 = st.columns(2)
        with c_b1:
            v1 = st.selectbox("Ottavo 1", ["Vincitore A", "Migliore Terza X"], key="v1")
            v2 = st.selectbox("Ottavo 2", ["Vincitore B", "Seconda C"], key="v2")
            q1 = st.selectbox("🏆 Quarto 1", [v1, v2], key="q1")
        with c_b2:
            st.info("Ripeti per tutti i rami per completare il bracket")

    with t4:
        st.header("🚀 Invio Finale")
        if st.button("SALVA PRONOSTICI", type="primary"):
            foglio = connetti()
            if foglio:
                # Trasforma i dati in stringa per il foglio
                payload = [nick, json.dumps(stats)]
                foglio.append_row(payload)
                st.success("Dati inviati! Palloncini per te!")
                st.balloons()
            else:
                st.error("Errore Database! Controlla il JSON nei Secrets di Streamlit.")

if is_admin:
    st.divider()
    st.subheader("⚙️ Pannello Admin Sbloccato")
    st.write("Inserisci i risultati reali qui...")
