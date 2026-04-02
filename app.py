import streamlit as st
import pandas as pd
import json
import gspread
import random
from google.oauth2.service_account import Credentials

# --- 1. CONFIGURAZIONE PAGINA E DARK THEME CSS ---
st.set_page_config(page_title="WC 2026 Dark Contest", layout="wide")

st.markdown("""
    <style>
    /* Sfondo globale scuro */
    .stApp { background-color: #0e1117; color: #ffffff; }
    
    /* Card dei Match */
    .match-card {
        background-color: #1d2129;
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 15px;
        text-align: center;
        margin-bottom: 20px;
        height: 280px; /* Altezza fissa per allineamento perfetto */
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    
    .team-name { font-size: 18px !important; font-weight: bold; color: #58a6ff; margin: 5px 0; }
    .vs-text { color: #8b949e; font-weight: bold; }
    
    /* Box Punteggi 1-X-2 */
    .pts-box {
        background-color: #0d1117;
        border: 1px solid #f85149;
        color: #f85149;
        padding: 8px;
        border-radius: 8px;
        font-weight: bold;
        font-size: 16px;
        margin-top: 10px;
    }

    /* Input numeri */
    .stNumberInput input {
        background-color: #0d1117 !important;
        color: white !important;
        font-size: 20px !important;
        border: 1px solid #30363d !important;
    }

    /* Login Centrato */
    .login-container { display: flex; justify-content: center; align-items: center; padding: 100px 0; }
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

# --- 3. CONNESSIONE GOOGLE SHEETS ---
def salva_dati(nick, dati_json):
    try:
        js = json.loads(st.secrets["service_account"])
        creds = Credentials.from_service_account_info(js, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
        client = gspread.authorize(creds)
        
        # --- RIGA 65: INSERISCI QUI IL TUO LINK ---
        URL_FOGLIO = "https://docs.google.com/spreadsheets/d/1palUSBw4IlBFzU4dKtgT0tnjPiPEtxIc6K-DK05vXG8/edit?gid=0#gid=0" 
        
        sh = client.open_by_url(URL_FOGLIO).sheet1
        sh.append_row([nick, dati_json])
        return True
    except Exception as e:
        st.error(f"Errore Database: {e}")
        return False

# --- 4. LOGICA TORNEO ---
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
    m = []
    for gid, teams in g.items():
        for h, a in [(0,1), (2,3), (0,2), (1,3), (0,3), (1,2)]:
            m.append({"gr": gid, "h": teams[h], "a": teams[a]})
    return g, m

G_TEAMS, MATCHES = get_data()

def get_flag(t):
    m = {"Messico": "mx", "Sudafrica": "za", "Sudcorea": "kr", "Repubblica Ceca": "cz", "Canada": "ca", "Bosnia Erzegovina": "ba", "Qatar": "qa", "Svizzera": "ch", "Brasile": "br", "Marocco": "ma", "Haiti": "ht", "Scozia": "gb-sct", "USA": "us", "Paraguay": "py", "Australia": "au", "Turchia": "tr", "Germania": "de", "Curacao": "cw", "Costa D'Avorio": "ci", "Ecuador": "ec", "Olanda": "nl", "Giappone": "jp", "Svezia": "se", "Tunisia": "tn", "Belgio": "be", "Egitto": "eg", "Iran": "ir", "Nuova Zelanda": "nz", "Spagna": "es", "Capo Verde": "cv", "Arabia Saudita": "sa", "Uruguay": "uy", "Francia": "fr", "Senegal": "sn", "Iraq": "iq", "Norvegia": "no", "Argentina": "ar", "Algeria": "dz", "Austria": "at", "Giordania": "jo", "Portogallo": "pt", "DR Congo": "cd", "Uzbekistan": "uz", "Colombia": "co", "Inghilterra": "gb-eng", "Croazia": "hr", "Ghana": "gh", "Panama": "pa", "Italia": "it"}
    return f"https://flagcdn.com/w160/{m.get(t, 'un')}.png"

# --- 5. HEADER (ADMIN A DESTRA) ---
col_h1, col_h2 = st.columns([9, 1])
with col_h2:
    admin_input = st.text_input("🔑", type="password", help="Area Admin")
    is_admin = (admin_input == "mondiali2026")

# --- 6. LOGIN CENTRATO ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

if not st.session_state.logged_in:
    _, center_col, _ = st.columns([1, 1, 1])
    with center_col:
        st.markdown("<h1 style='text-align:center;'>🏆 WC 2026 LOGIN</h1>", unsafe_allow_html=True)
        nick = st.text_input("Inserisci il tuo Nickname per partecipare:")
        if st.button("ENTRA NEL CONTEST", use_container_width=True):
            if nick:
                st.session_state.nickname = nick
                st.session_state.logged_in = True
                st.rerun()
else:
    # --- APP REALE DOPO LOGIN ---
    st.write(f"Partecipante: **{st.session_state.nickname}**")
    tab1, tab2, tab3, tab4 = st.tabs(["🌍 Gironi", "📊 Classifiche", "⚔️ Bracket", "🚀 Invia"])

    with tab1:
        if st.button("🎲 Compila Automaticamente", type="secondary"):
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
                    # Correzione Ranking: Vittoria casa (1) = Ranking Ospite | Vittoria trasferta (2) = Ranking Casa
                    p1 = RANKING[m['a']]
                    p2 = RANKING[m['h']]
                    px = (p1 + p2) // 2
                    
                    with cols[c]:
                        st.markdown(f"""
                        <div class="match-card">
                            <div style="color:#f85149; font-weight:bold; font-size:12px;">GRUPPO {m['gr']}</div>
                            <div style="display:flex; justify-content:space-around; align-items:center;">
                                <div style="width:40%;"><img src="{get_flag(m['h'])}" width="50"><div class="team-name">{m['h']}</div></div>
                                <div class="vs-text">VS</div>
                                <div style="width:40%;"><img src="{get_flag(m['a'])}" width="50"><div class="team-name">{m['a']}</div></div>
                            </div>
                        """, unsafe_allow_html=True)
                        ci = st.columns(2)
                        with ci[0]: h_res = st.number_input("H", 0, 9, key=f"h_{idx}", label_visibility="collapsed")
                        with ci[1]: a_res = st.number_input("A", 0, 9, key=f"a_{idx}", label_visibility="collapsed")
                        st.markdown(f"<div class='pts-box'>1: {p1} | X: {px} | 2: {p2}</div></div>", unsafe_allow_html=True)

    with tab2:
        st.header("Classifiche in tempo reale")
        stats = {g: {t: {"Pt":0, "DR":0, "GF":0} for t in ts} for g, ts in G_TEAMS.items()}
        for i, m in enumerate(MATCHES):
            h_g = st.session_state.get(f"h_{i}", 0)
            a_g = st.session_state.get(f"a_{i}", 0)
            sh, sa = stats[m['gr']][m['h']], stats[m['gr']][m['a']]
            sh["GF"] += h_g; sa["GF"] += a_g
            sh["DR"] += (h_g-a_g); sa["DR"] += (a_g-h_g)
            if h_g > a_g: sh["Pt"] += 3
            elif a_g > h_g: sa["Pt"] += 3
            else: sh["Pt"] += 1; sa["Pt"] += 1

        for r in range(0, 12, 3):
            cols_g = st.columns(3)
            for k in range(3):
                gid = list(G_TEAMS.keys())[r+k]
                df = pd.DataFrame(stats[gid]).T.sort_values(["Pt","DR","GF"], ascending=False)
                with cols_g[k]:
                    st.subheader(f"Girone {gid}")
                    st.table(df)

    with tab3:
        st.header("⚔️ Bracket ad eliminazione diretta")
        st.info("Il bracket si popola automaticamente in base alle classifiche dei gironi.")
        
        # ESTRAZIONE TOP 2 + 8 MIGLIORI TERZE
        all_thirds = []
        final_ranking = {}
        for gid, teams_stat in stats.items():
            df_g = pd.DataFrame(teams_stat).T.sort_values(["Pt","DR","GF"], ascending=False)
            final_ranking[gid] = df_g.index.tolist()
            all_thirds.append({"t": df_g.index[2], "Pt": df_g.iloc[2]["Pt"], "DR": df_g.iloc[2]["DR"], "GF": df_g.iloc[2]["GF"], "gr": gid})
        
        best_thirds = pd.DataFrame(all_thirds).sort_values(["Pt","DR","GF"], ascending=False).head(8)["t"].tolist()
        
        st.subheader("Accoppiamenti Ottavi (Esempio basato su Regole)")
        # Inseriamo i primi match basati sulla tua matrice
        col_b1, col_b2 = st.columns(2)
        with col_b1:
            match1 = [final_ranking["A"][1], final_ranking["C"][1]]
            st.write(f"**Ottavo 1:** {match1[0]} vs {match1[1]}")
            v1 = st.selectbox("Vincitore Ottavo 1", match1)
        with col_b2:
            match2 = [final_ranking["D"][0], best_thirds[0] if len(best_thirds)>0 else "3° Gruppo"]
            st.write(f"**Ottavo 2:** {match2[0]} vs {match2[1]}")
            v2 = st.selectbox("Vincitore Ottavo 2", match2)
        
        st.divider()
        st.markdown(f"<h2 style='text-align:center;'>VINCITORE FINALE: {v1}</h2>", unsafe_allow_html=True)

    with tab4:
        st.header("Invia i tuoi Pronostici")
        if st.button("🚀 SALVA DEFINITIVAMENTE", type="primary", use_container_width=True):
            if salva_dati(st.session_state.nickname, "Risultati Completi"):
                st.balloons()
                st.success("Pronostici salvati nel
