import streamlit as st
import pandas as pd
import json
import gspread
import random
from google.oauth2.service_account import Credentials

# --- 1. CONFIGURAZIONE E STILE DARK ---
st.set_page_config(page_title="WC 2026 Dark Contest", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #ffffff; }
    
    /* Card Match nel quadrato */
    .match-card {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 10px;
        padding: 15px;
        text-align: center;
        height: 280px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        margin-bottom: 20px;
    }
    
    .team-name { font-size: 18px !important; font-weight: bold; color: #c9d1d9; margin: 5px 0; }
    
    /* Box Punteggi 1-X-2 (Invertiti) */
    .pts-box {
        background-color: #0d1117;
        border: 1px solid #f85149;
        color: #f85149;
        padding: 5px;
        border-radius: 5px;
        font-weight: bold;
        font-size: 15px;
        margin-top: 10px;
    }

    .stNumberInput input {
        background-color: #0d1117 !important;
        color: #ffffff !important;
        font-size: 20px !important;
        border: 1px solid #30363d !important;
        text-align: center;
    }

    /* Admin in alto a DX */
    .admin-container { position: absolute; top: -50px; right: 0; width: 120px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. RANKING FIFA UFFICIALE ---
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
def salva_dati(nick, dati_finale):
    try:
        js = json.loads(st.secrets["service_account"])
        creds = Credentials.from_service_account_info(js, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
        client = gspread.authorize(creds)
        
        # --- RIGA 65: LINK FOGLIO ---
        URL_FOGLIO = "https://docs.google.com/spreadsheets/d/1palUSBw4IlBFzU4dKtgT0tnjPiPEtxIc6K-DK05vXG8/edit?gid=0#gid=0" 
        
        sh = client.open_by_url(URL_FOGLIO).sheet1
        sh.append_row([nick, json.dumps(dati_finale)])
        return True
    except Exception as e:
        st.error(f"Errore DB: {e}")
        return False

# --- 4. STRUTTURA TORNEO ---
@st.cache_data
def load_data():
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
    for gid, ts in g.items():
        for h, a in [(0,1), (2,3), (0,2), (1,3), (0,3), (1,2)]:
            m.append({"gr": gid, "h": ts[h], "a": ts[a]})
    return g, m

G_TEAMS, MATCHES = load_data()

def get_flag(t):
    m = {"Messico": "mx", "Sudafrica": "za", "Sudcorea": "kr", "Repubblica Ceca": "cz", "Canada": "ca", "Bosnia Erzegovina": "ba", "Qatar": "qa", "Svizzera": "ch", "Brasile": "br", "Marocco": "ma", "Haiti": "ht", "Scozia": "gb-sct", "USA": "us", "Paraguay": "py", "Australia": "au", "Turchia": "tr", "Germania": "de", "Curacao": "cw", "Costa D'Avorio": "ci", "Ecuador": "ec", "Olanda": "nl", "Giappone": "jp", "Svezia": "se", "Tunisia": "tn", "Belgio": "be", "Egitto": "eg", "Iran": "ir", "Nuova Zelanda": "nz", "Spagna": "es", "Capo Verde": "cv", "Arabia Saudita": "sa", "Uruguay": "uy", "Francia": "fr", "Senegal": "sn", "Iraq": "iq", "Norvegia": "no", "Argentina": "ar", "Algeria": "dz", "Austria": "at", "Giordania": "jo", "Portogallo": "pt", "DR Congo": "cd", "Uzbekistan": "uz", "Colombia": "co", "Inghilterra": "gb-eng", "Croazia": "hr", "Ghana": "gh", "Panama": "pa", "Italia": "it"}
    return f"https://flagcdn.com/w160/{m.get(t, 'un')}.png"

# --- 5. INTERFACCIA ---
# Admin in alto a DX
c_top1, c_top2 = st.columns([9, 1])
with c_top2:
    adm_p = st.text_input("🔑", type="password")
    is_admin = (adm_p == "mondiali2026")

if 'logged_in' not in st.session_state: st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.markdown("<br><br>", unsafe_allow_html=True)
    _, login_col, _ = st.columns([1, 1, 1])
    with login_col:
        st.markdown("<h1 style='text-align:center;'>🏆 WC 2026 CONTEST</h1>", unsafe_allow_html=True)
        nick = st.text_input("Scegli un Nickname per iniziare:")
        if st.button("ACCEDI AL GIOCO", use_container_width=True):
            if nick:
                st.session_state.nickname = nick
                st.session_state.logged_in = True
                st.rerun()
else:
    st.markdown(f"### Benvenuto, {st.session_state.nickname}")
    t1, t2, t3, t4 = st.tabs(["🌍 Gironi", "📊 Classifiche", "⚔️ Bracket", "🚀 Invia"])

    with t1:
        if st.button("Compila Automaticamente", type="primary"):
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
                    # RANKING INVERTITO: Segno 1 = Ranking Away | Segno 2 = Ranking Home
                    pt1 = RANKING[m['a']]
                    pt2 = RANKING[m['h']]
                    ptx = (pt1 + pt2) // 2
                    with cols[c]:
                        st.markdown(f"""
                        <div class="match-card">
                            <div style="color:#8b949e; font-size:12px; font-weight:bold;">GIRONE {m['gr']}</div>
                            <div style="display:flex; justify-content:space-around; align-items:center; margin-top:10px;">
                                <div style="width:40%"><img src="{get_flag(m['h'])}" width="50"><div class="team-name">{m['h']}</div></div>
                                <div style="color:#30363d;">VS</div>
                                <div style="width:40%"><img src="{get_flag(m['a'])}" width="50"><div class="team-name">{m['a']}</div></div>
                            </div>
                        """, unsafe_allow_html=True)
                        ci = st.columns(2)
                        with ci[0]: h_val = st.number_input("H", 0, 9, key=f"h_{idx}", label_visibility="collapsed")
                        with ci[1]: a_val = st.number_input("A", 0, 9, key=f"a_{idx}", label_visibility="collapsed")
                        st.markdown(f"<div class='pts-box'>1: {pt1} | X: {ptx} | 2: {pt2}</div></div>", unsafe_allow_html=True)

    with t2:
        # Calcolo classifiche
        stats = {g: {t: {"Pt":0, "DR":0, "GF":0} for t in ts} for g, ts in G_TEAMS.items()}
        for i, m in enumerate(MATCHES):
            h_g, a_g = st.session_state.get(f"h_{i}",0), st.session_state.get(f"a_{i}",0)
            sh, sa = stats[m['gr']][m['h']], stats[m['gr']][m['a']]
            sh["GF"] += h_g; sa["GF"] += a_g
            sh["DR"] += (h_g-a_g); sa["DR"] += (a_g-h_g)
            if h_g > a_g: sh["Pt"] += 3
            elif a_g > h_g: sa["Pt"] += 3
            else: sh["Pt"] += 1; sa["Pt"] += 1

        for r in range(0, 12, 3):
            cg = st.columns(3)
            for k in range(3):
                gid = list(G_TEAMS.keys())[r+k]
                df = pd.DataFrame(stats[gid]).T.sort_values(["Pt","DR","GF"], ascending=False)
                with cg[k]:
                    st.subheader(f"Gruppo {gid}")
                    st.table(df)

    with t3:
        st.header("⚔️ Bracket ad eliminazione diretta")
        # 1. Determina Top 2 e Terze
        final_ranks = {}
        thirds = []
        for gid, teams in stats.items():
            df = pd.DataFrame(teams).T.sort_values(["Pt","DR","GF"], ascending=False)
            final_ranks[gid] = df.index.tolist()
            thirds.append({"t": df.index[2], "Pt": df.iloc[2]["Pt"], "DR": df.iloc[2]["DR"], "GF": df.iloc[2]["GF"], "gr": gid})
        
        # 2. Migliori 8 terze
        best_3rd = pd.DataFrame(thirds).sort_values(["Pt","DR","GF"], ascending=False).head(8)
        b3_names = best_3rd["t"].tolist()
        b3_groups = "".join(sorted(best_3rd["gr"].tolist()))
        
        st.success(f"Combinazione Terze: {b3_groups}")
        
        # 3. Accoppiamenti (Esempio Matrice)
        # Qui potresti mappare b3_groups alla tua matrice RTF
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**Ottavo 1:** {final_ranks['A'][1]} vs {final_ranks['C'][1]}")
            v1 = st.selectbox("Vincitore Ottavo 1", [final_ranks['A'][1], final_ranks['C'][1]])
            
            st.markdown(f"**Ottavo 2:** {final_ranks['D'][0]} vs {b3_names[0]}")
            v2 = st.selectbox("Vincitore Ottavo 2", [final_ranks['D'][0], b3_names[0]])
        
        with col2:
            st.markdown(f"**Quarto 1:** {v1} vs {v2}")
            vincitore = st.selectbox("🏆 CAMPIONE", [v1, v2])

    with t4:
        if st.button("🚀 INVIA TUTTO AL DATABASE", use_container_width=True):
            if salva_dati(st.session_state.nickname, {"risultati": "completati"}):
                st.balloons()
                st.success("Pronostici salvati con successo!")

if is_admin:
    st.sidebar.subheader("Pannello Admin")
    st.sidebar.write("Gestione risultati reali...")
