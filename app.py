import streamlit as st
import pandas as pd
import json
import gspread
import random
from google.oauth2.service_account import Credentials

# --- 1. CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="WC 2026 Contest PRO", layout="wide")

# LOGO E COLORI
LOGO_URL = "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a7/2026_FIFA_World_Cup_logo.svg/512px-2026_FIFA_World_Cup_logo.svg.png"

# CSS: STILE DARK AD ALTO CONTRASTO
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap');
    
    .stApp {{ background-color: #0e1117; color: #ffffff; font-family: 'Inter', sans-serif; }}
    
    /* Ingrandimento TAB e contrasto */
    button[data-baseweb="tab"] p {{ font-size: 20px !important; font-weight: 700 !important; color: #adbac7 !important; }}
    button[data-baseweb="tab"][aria-selected="true"] p {{ color: #58a6ff !important; }}

    /* Card Partite */
    .match-card {{
        background: #161b22; border-radius: 12px; padding: 20px; border: 1px solid #30363d; margin-bottom: 15px;
    }}
    
    /* Badge Ranking (Punteggi 1X2) */
    .ranking-badge {{
        background: #238636; color: #ffffff; border-radius: 6px; font-size: 12px; font-weight: 800;
        padding: 6px; text-align: center; margin-bottom: 10px;
    }}

    /* Input Numerici (Grandi e Bianchi) */
    input[type="number"] {{
        background-color: #0d1117 !important; color: #ffffff !important;
        font-size: 24px !important; font-weight: 900 !important; border: 2px solid #30363d !important;
        text-align: center !important; border-radius: 8px !important;
    }}
    
    .team-label {{ font-size: 14px; font-weight: 700; color: #ffffff; text-align: center; }}
    .vs-text {{ color: #8b949e; font-weight: 900; font-size: 20px; }}
</style>
""", unsafe_allow_html=True)

# --- 2. DATI E RANKING ---
RANKING = {
    "Messico": 15, "Sudafrica": 61, "Sudcorea": 22, "Repubblica Ceca": 44, "Canada": 27, "Bosnia Erzegovina": 71, "Qatar": 58, "Svizzera": 17,
    "Brasile": 5, "Marocco": 11, "Haiti": 84, "Scozia": 36, "USA": 14, "Paraguay": 39, "Australia": 26, "Turchia": 25, "Germania": 9, "Curacao": 82,
    "Costa D'Avorio": 42, "Ecuador": 23, "Olanda": 7, "Giappone": 18, "Svezia": 43, "Tunisia": 40, "Belgio": 8, "Egitto": 34, "Iran": 20, 
    "Nuova Zelanda": 86, "Spagna": 1, "Capo Verde": 68, "Arabia Saudita": 60, "Uruguay": 16, "Francia": 3, "Senegal": 19, "Iraq": 58, 
    "Norvegia": 29, "Argentina": 2, "Algeria": 35, "Austria": 24, "Giordania": 66, "Portogallo": 6, "DR Congo": 56, "Uzbekistan": 50, 
    "Colombia": 13, "Inghilterra": 4, "Croazia": 10, "Ghana": 72, "Panama": 30, "Italia": 13
}

@st.cache_data
def get_matches_data():
    g = {
        "A": ["Messico", "Sudafrica", "Sudcorea", "Repubblica Ceca"], "B": ["Canada", "Bosnia Erzegovina", "Qatar", "Svizzera"],
        "C": ["Brasile", "Marocco", "Haiti", "Scozia"], "D": ["USA", "Paraguay", "Australia", "Turchia"],
        "E": ["Germania", "Curacao", "Costa D'Avorio", "Ecuador"], "F": ["Olanda", "Giappone", "Svezia", "Tunisia"],
        "G": ["Belgio", "Egitto", "Iran", "Nuova Zelanda"], "H": ["Spagna", "Capo Verde", "Arabia Saudita", "Uruguay"],
        "I": ["Francia", "Senegal", "Iraq", "Norvegia"], "J": ["Argentina", "Algeria", "Austria", "Giordania"],
        "K": ["Portogallo", "DR Congo", "Uzbekistan", "Colombia"], "L": ["Inghilterra", "Croazia", "Ghana", "Panama"]
    }
    ml = []
    for gid, teams in g.items():
        for h, a in [(0, 1), (2, 3), (0, 2), (1, 3), (0, 3), (1, 2)]:
            ml.append({"gr": gid, "h": teams[h], "a": teams[a]})
    return g, ml

G_TEAMS, MATCHES = get_matches_data()

def get_flag(t):
    if not t or t == "???" or t == "Non assegnato": return "https://flagcdn.com/w160/un.png"
    m = {"Messico": "mx", "Sudafrica": "za", "Sudcorea": "kr", "Repubblica Ceca": "cz", "Canada": "ca", "Bosnia Erzegovina": "ba", "Qatar": "qa", "Svizzera": "ch", "Brasile": "br", "Marocco": "ma", "Haiti": "ht", "Scozia": "gb-sct", "USA": "us", "Paraguay": "py", "Australia": "au", "Turchia": "tr", "Germania": "de", "Curacao": "cw", "Costa D'Avorio": "ci", "Ecuador": "ec", "Olanda": "nl", "Giappone": "jp", "Svezia": "se", "Tunisia": "tn", "Belgio": "be", "Egitto": "eg", "Iran": "ir", "Nuova Zelanda": "nz", "Spagna": "es", "Capo Verde": "cv", "Arabia Saudita": "sa", "Uruguay": "uy", "Francia": "fr", "Senegal": "sn", "Iraq": "iq", "Norvegia": "no", "Argentina": "ar", "Algeria": "dz", "Austria": "at", "Giordania": "jo", "Portogallo": "pt", "DR Congo": "cd", "Uzbekistan": "uz", "Colombia": "co", "Inghilterra": "gb-eng", "Croazia": "hr", "Ghana": "gh", "Panama": "pa", "Italia": "it"}
    return f"https://flagcdn.com/w160/{m.get(t, 'un')}.png"

# --- 3. GOOGLE SHEETS CONNECTION ---
def salva_dati_google(sheet_name, nick, dati):
    try:
        info = json.loads(st.secrets["service_account"])
        creds = Credentials.from_service_account_info(info, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
        client = gspread.authorize(creds)
        # ID FOGLIO (Estrailo dal tuo URL)
        URL_FOGLIO = "https://docs.google.com/spreadsheets/d/1palUSBw4IlBFzU4dKtgT0tnjPiPEtxIc6K-DK05vXG8/edit?gid=0#gid=0"
        sh = client.open_by_url(URL_FOGLIO)
        try: ws = sh.worksheet(sheet_name)
        except: ws = sh.get_worksheet(0)
        ws.append_row([nick, json.dumps(dati)])
        return True
    except Exception as e:
        st.error(f"Errore Google Sheets: {e}")
        return False

# --- 4. LOGICA CLASSICHE ---
def calcola_classifiche():
    res = {g: {t: {"Pt": 0, "DR": 0, "GF": 0} for t in ts} for g, ts in G_TEAMS.items()}
    for i, m in enumerate(MATCHES):
        h_g = st.session_state.get(f"h_{i}", 0)
        a_g = st.session_state.get(f"a_{i}", 0)
        sh, sa = res[m['gr']][m['h']], res[m['gr']][m['a']]
        sh["GF"] += h_g; sa["GF"] += a_g
        sh["DR"] += (h_g - a_g); sa["DR"] += (a_g - h_g)
        if h_g > a_g: sh["Pt"] += 3
        elif a_g > h_g: sa["Pt"] += 3
        else: sh["Pt"] += 1; sa["Pt"] += 1
    
    final_ranks = {}
    thirds = []
    for gid, ts in res.items():
        df = pd.DataFrame(ts).T.sort_values(["Pt", "DR", "GF"], ascending=False)
        final_ranks[gid] = df.index.tolist()
        thirds.append({"team": df.index[2], "Pt": df.iloc[2]["Pt"], "gr": gid})
    return final_ranks, pd.DataFrame(thirds).sort_values("Pt", ascending=False).head(8), res

# --- 5. INTERFACCIA ---
col_logo, col_adm = st.columns([7, 3])
with col_logo: st.image(LOGO_URL, width=200)
with col_adm: 
    adm_pass = st.text_input("🔓 Admin Area", type="password", placeholder="Password...")
    is_admin = (adm_pass == "mondiali2026")

user_nick = st.text_input("👤 Nickname Partecipante:", placeholder="Inserisci il tuo nome...")

if user_nick:
    tab_list = ["🌍 Gironi", "📊 Classifiche", "⚔️ Bracket", "🚀 Invia"]
    if is_admin: tab_list.append("⚙️ Admin & Ranking")
    tabs = st.tabs(tab_list)

    # --- TAB GIRONI ---
    with tabs[0]:
        st.info("Inserisci i risultati. I punti 1-X-2 sono calcolati in base al Ranking FIFA.")
        if st.button("🪄 Compilazione Automatica (Risultati casuali)"):
            for i in range(72):
                st.session_state[f"h_{i}"] = random.randint(0, 4)
                st.session_state[f"a_{i}"] = random.randint(0, 4)
            st.rerun()

        for r in range(18):
            cols = st.columns(4)
            for c in range(4):
                idx = r * 4 + c
                if idx < 72:
                    m = MATCHES[idx]
                    p1, p2, px = RANKING[m['a']], RANKING[m['h']], (RANKING[m['h']]+RANKING[m['a']])//2
                    with cols[c]:
                        with st.container(border=True):
                            st.markdown(f"<div class='ranking-badge'>PUNTI: 1={p1} | X={px} | 2={p2}</div>", unsafe_allow_html=True)
                            
                            # Layout Orizzontale Score
                            sc1, sc_in1, sc_vs, sc_in2, sc2 = st.columns([1, 1.3, 0.4, 1.3, 1])
                            sc1.image(get_flag(m['h']), width=35)
                            sc_in1.number_input("H", 0, 9, key=f"h_{idx}", value=st.session_state.get(f"h_{idx}", 0), label_visibility="collapsed")
                            sc_vs.markdown("<p style='padding-top:10px; text-align:center;'>-</p>", unsafe_allow_html=True)
                            sc_in2.number_input("A", 0, 9, key=f"a_{idx}", value=st.session_state.get(f"a_{idx}", 0), label_visibility="collapsed")
                            sc2.image(get_flag(m['a']), width=35)
                            
                            st.markdown(f"<p class='team-label'>{m['h']} vs {m['a']}</p>", unsafe_allow_html=True)

    # --- TAB BRACKET TENNISTICO ---
    with tabs[2]:
        ranks, th_df, _ = calcola_classifiche()
        th_dict = {row['gr']: row['team'] for _, row in th_df.iterrows()}
        
        def render_match_box(t1, t2, mid, label):
            with st.container(border=True):
                st.caption(label)
                c1, c2 = st.columns(2)
                with c1:
                    st.image(get_flag(t1), width=40)
                    if st.button(f"{t1}", key=f"btn1_{mid}", use_container_width=True, type="primary" if st.session_state.get(mid) == t1 else "secondary"):
                        st.session_state[mid] = t1; st.rerun()
                with c2:
                    st.image(get_flag(t2), width=40)
                    if st.button(f"{t2}", key=f"btn2_{mid}", use_container_width=True, type="primary" if st.session_state.get(mid) == t2 else "secondary"):
                        st.session_state[mid] = t2; st.rerun()
                return st.session_state.get(mid, "???")

        # Layout Tennistico SX -> DX
        st.subheader("⚔️ Tabellone Eliminazione Diretta")
        c_sed, c_ott, c_qua, c_fin = st.columns([1.2, 1.1, 1.1, 1.4])
        
        with c_sed:
            st.write("📌 Sedicesimi")
            v_s1 = render_match_box(ranks["A"][1], ranks["C"][1], "S1", "Match 1")
            v_s2 = render_match_box(ranks["D"][0], "3rd Group", "S2", "Match 2")

        with c_ott:
            st.write("🎯 Ottavi")
            v_o1 = render_match_box(v_s1, v_s2, "O1", "Ottavo 1")

        with c_qua:
            st.write("💎 Quarti")
            v_q1 = render_match_box(v_o1, "TBD", "Q1", "Quarto 1")

        with c_fin:
            st.write("🔥 Semifinali e Finale")
            v_semi1 = render_match_box(v_q1, "TBD", "semi1", "Semi 1")
            st.divider()
            campione = render_match_box(v_semi1, "Finalista 2", "win", "🏆 CAMPIONE")
            st.session_state["campione"] = campione
            if campione != "???" and campione != "": st.balloons()

    # --- TAB AREA ADMIN ---
    if is_admin:
        with tabs[-1]:
            st.header("⚙️ Area Gestione Admin")
            if st.button("🪄 Auto-compila Risultati Reali (Test)"):
                for i in range(72):
                    st.session_state[f"adm_h_{i}"] = random.randint(0, 3)
                    st.session_state[f"adm_a_{i}"] = random.randint(0, 3)
                st.rerun()
            
            st.subheader("📊 Classifica Partecipanti")
            # Qui andrebbe la logica di calcolo punti leggendo il foglio 'Pronostici'
            st.info("I punti verranno calcolati confrontando i pronostici salvati con i risultati reali.")

            with st.expander("Inserisci Risultati Reali"):
                for i, m in enumerate(MATCHES):
                    c1, c2 = st.columns(2)
                    st.session_state[f"adm_h_{i}"] = c1.number_input(f"{m['h']}", 0, 9, key=f"ah_{i}")
                    st.session_state[f"adm_a_{i}"] = c2.number_input(f"{m['a']}", 0, 9, key=f"aa_{i}")

    # --- TAB INVIO ---
    with tabs[3]:
        st.write("### 🚀 Pronti per l'invio?")
        if st.button("SALVA PRONOSTICI DEFINITIVAMENTE", type="primary", use_container_width=True):
            payload = {
                "Gironi": {f"M_{i}": [st.session_state.get(f"h_{i}"), st.session_state.get(f"a_{i}")] for i in range(72)},
                "Vincitore": st.session_state.get("campione")
            }
            if salva_dati_google("Pronostici", user_nick, payload):
                st.balloons()
                st.success("Tutto salvato! In bocca al lupo!")
