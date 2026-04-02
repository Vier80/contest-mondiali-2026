import streamlit as st
import pandas as pd
import json
import gspread
import random
from google.oauth2.service_account import Credentials

# --- 1. CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="WC 2026 Prediction PRO", layout="wide")

# LOGO UFFICIALE
LOGO_URL = "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a7/2026_FIFA_World_Cup_logo.svg/512px-2026_FIFA_World_Cup_logo.svg.png"

# CSS: DESIGN DARK PROFESSIONALE
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap');
    
    .stApp {{ background-color: #0b0e14; color: #e2e8f0; font-family: 'Inter', sans-serif; }}
    
    /* Ingrandimento TAB */
    button[data-baseweb="tab"] p {{ font-size: 22px !important; font-weight: 700 !important; }}
    button[data-baseweb="tab"][aria-selected="true"] {{ border-bottom-color: #00f2ff !important; }}
    button[data-baseweb="tab"][aria-selected="true"] p {{ color: #00f2ff !important; }}

    /* Card Partite Professionale */
    .match-card {{
        background: #1a1f29; border-radius: 15px; padding: 20px; border: 1px solid #2d3748;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.5); margin-bottom: 20px;
    }}
    
    /* Punteggi Ranking */
    .ranking-box {{
        background: linear-gradient(90deg, #00c6ff 0%, #0072ff 100%);
        color: white; border-radius: 8px; font-size: 12px; font-weight: 800;
        padding: 5px 10px; text-align: center; margin-bottom: 15px;
    }}

    /* Input Numerici Estetici */
    input[type="number"] {{
        background-color: #0f172a !important; color: #ffffff !important;
        font-size: 26px !important; font-weight: 900 !important; border: 2px solid #334155 !important;
        text-align: center !important; border-radius: 10px !important; width: 80px !important;
    }}
    
    .team-label {{ font-size: 15px; font-weight: 700; color: #ffffff; text-align: center; margin-top: 10px; }}
    .vs-line {{ color: #64748b; font-weight: 900; font-size: 24px; padding-top: 10px; }}
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

def get_groups():
    return {
        "A": ["Messico", "Sudafrica", "Sudcorea", "Repubblica Ceca"], "B": ["Canada", "Bosnia Erzegovina", "Qatar", "Svizzera"],
        "C": ["Brasile", "Marocco", "Haiti", "Scozia"], "D": ["USA", "Paraguay", "Australia", "Turchia"],
        "E": ["Germania", "Curacao", "Costa D'Avorio", "Ecuador"], "F": ["Olanda", "Giappone", "Svezia", "Tunisia"],
        "G": ["Belgio", "Egitto", "Iran", "Nuova Zelanda"], "H": ["Spagna", "Capo Verde", "Arabia Saudita", "Uruguay"],
        "I": ["Francia", "Senegal", "Iraq", "Norvegia"], "J": ["Argentina", "Algeria", "Austria", "Giordania"],
        "K": ["Portogallo", "DR Congo", "Uzbekistan", "Colombia"], "L": ["Inghilterra", "Croazia", "Ghana", "Panama"]
    }

def get_matches():
    g = get_groups()
    ml = []
    for gid, teams in g.items():
        for h, a in [(0, 1), (2, 3), (0, 2), (1, 3), (0, 3), (1, 2)]:
            ml.append({"gr": gid, "h": teams[h], "a": teams[a]})
    return ml

MATCHES = get_matches()

def get_flag(t):
    if not t or t == "???" or t == "TBD": return "https://flagcdn.com/w160/un.png"
    m = {"Messico": "mx", "Sudafrica": "za", "Sudcorea": "kr", "Repubblica Ceca": "cz", "Canada": "ca", "Bosnia Erzegovina": "ba", "Qatar": "qa", "Svizzera": "ch", "Brasile": "br", "Marocco": "ma", "Haiti": "ht", "Scozia": "gb-sct", "USA": "us", "Paraguay": "py", "Australia": "au", "Turchia": "tr", "Germania": "de", "Curacao": "cw", "Costa D'Avorio": "ci", "Ecuador": "ec", "Olanda": "nl", "Giappone": "jp", "Svezia": "se", "Tunisia": "tn", "Belgio": "be", "Egitto": "eg", "Iran": "ir", "Nuova Zelanda": "nz", "Spagna": "es", "Capo Verde": "cv", "Arabia Saudita": "sa", "Uruguay": "uy", "Francia": "fr", "Senegal": "sn", "Iraq": "iq", "Norvegia": "no", "Argentina": "ar", "Algeria": "dz", "Austria": "at", "Giordania": "jo", "Portogallo": "pt", "DR Congo": "cd", "Uzbekistan": "uz", "Colombia": "co", "Inghilterra": "gb-eng", "Croazia": "hr", "Ghana": "gh", "Panama": "pa", "Italia": "it"}
    return f"https://flagcdn.com/w160/{m.get(t, 'un')}.png"

# --- 3. LOGICA DATABASE ---
def salva_gspread(sheet_name, nick, data):
    try:
        cred_info = json.loads(st.secrets["service_account"])
        creds = Credentials.from_service_account_info(cred_info, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
        client = gspread.authorize(creds)
        URL_FOGLIO = "https://docs.google.com/spreadsheets/d/1palUSBw4IlBFzU4dKtgT0tnjPiPEtxIc6K-DK05vXG8/edit?gid=0#gid=0"
        sh = client.open_by_url(URL_FOGLIO)
        ws = sh.worksheet(sheet_name) if sheet_name in [w.title for w in sh.worksheets()] else sh.get_worksheet(0)
        ws.append_row([nick, json.dumps(data)])
        return True
    except Exception as e:
        st.error(f"Errore Google Sheets: {e}")
        return False

# --- 4. CALCOLO CLASSIFICHE ---
def update_standings():
    groups = get_groups()
    stats = {g: {t: {"Pt": 0, "DR": 0, "GF": 0} for t in ts} for g, ts in groups.items()}
    for i, m in enumerate(MATCHES):
        h_g = st.session_state.get(f"h_{i}", 0)
        a_g = st.session_state.get(f"a_{i}", 0)
        sh, sa = stats[m['gr']][m['h']], stats[m['gr']][m['a']]
        sh["GF"] += h_g; sa["GF"] += a_g
        sh["DR"] += (h_g - a_g); sa["DR"] += (a_g - h_g)
        if h_g > a_g: sh["Pt"] += 3
        elif a_g > h_g: sa["Pt"] += 3
        else: sh["Pt"] += 1; sa["Pt"] += 1
    
    ranks = {}
    for g, ts in stats.items():
        ranks[g] = pd.DataFrame(ts).T.sort_values(["Pt", "DR", "GF"], ascending=False).index.tolist()
    return ranks, stats

# --- 5. INTERFACCIA ---
st.image(LOGO_URL, width=140)
st.title("🏆 World Cup 2026 Prediction PRO")

# Login Admin in alto a DX
with st.sidebar:
    st.write("### 🔒 Area Riservata")
    admin_pw = st.text_input("Password Admin", type="password")
    is_admin = (admin_pw == "mondiali2026")

user_nick = st.text_input("👤 Nickname Partecipante:", placeholder="Inserisci nome...")

if user_nick:
    tab_labels = ["🌍 Gironi", "📊 Classifiche", "⚔️ Bracket", "🚀 Invia"]
    if is_admin: tab_labels.append("⚙️ Admin")
    tabs = st.tabs(tab_labels)

    with tabs[0]: # GIRONI
        st.subheader("Fase a Gironi")
        if st.button("🪄 Compilazione Automatica Risultati"):
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
                        st.markdown(f"""
                        <div class="match-card">
                            <div class="ranking-box">Punti: 1={p1} | X={px} | 2={p2}</div>
                        </div>
                        """, unsafe_allow_html=True)
                        c1, s1, vs, s2, c2 = st.columns([1, 1.5, 0.5, 1.5, 1])
                        c1.image(get_flag(m['h']), width=35)
                        st.session_state[f"h_{idx}"] = s1.number_input("H", 0, 9, key=f"in_h_{idx}", value=st.session_state.get(f"h_{idx}", 0), label_visibility="collapsed")
                        vs.markdown("<div class='vs-line'>-</div>", unsafe_allow_html=True)
                        st.session_state[f"a_{idx}"] = s2.number_input("A", 0, 9, key=f"in_a_{idx}", value=st.session_state.get(f"a_{idx}", 0), label_visibility="collapsed")
                        c2.image(get_flag(m['a']), width=35)
                        st.markdown(f"<div class='team-label'>{m['h']} vs {m['a']}</div>", unsafe_allow_html=True)

    with tabs[1]: # CLASSIFICHE
        ranks, stats = update_standings()
        for i in range(0, 12, 3):
            cols = st.columns(3)
            for k in range(3):
                gid = list(get_groups().keys())[i+k]
                df = pd.DataFrame(stats[gid]).T.sort_values(["Pt", "DR", "GF"], ascending=False)
                cols[k].write(f"### Gruppo {gid}")
                cols[k].dataframe(df.style.background_gradient(cmap='Blues'), use_container_width=True)

    with tabs[2]: # BRACKET
        ranks, _ = update_standings()
        
        def bracket_match(t1, t2, b_id, label):
            with st.container(border=True):
                st.caption(label)
                col1, col2 = st.columns(2)
                with col1:
                    st.image(get_flag(t1), width=45)
                    if st.button(f"{t1}", key=f"bt1_{b_id}", use_container_width=True, type="primary" if st.session_state.get(b_id) == t1 else "secondary"):
                        st.session_state[b_id] = t1; st.rerun()
                with col2:
                    st.image(get_flag(t2), width=45)
                    if st.button(f"{t2}", key=f"bt2_{b_id}", use_container_width=True, type="primary" if st.session_state.get(b_id) == t2 else "secondary"):
                        st.session_state[b_id] = t2; st.rerun()
                return st.session_state.get(b_id, "TBD")

        if st.button("🪄 Compilazione Automatica Bracket"):
            st.session_state["S1"] = random.choice([ranks["A"][1], ranks["C"][1]])
            st.session_state["S2"] = ranks["D"][0]
            st.session_state["O1"] = random.choice([st.session_state["S1"], st.session_state["S2"]])
            # ... simula resto del bracket
            st.rerun()

        st.write("### ⚔️ Tabellone Eliminazione Diretta")
        c_sed, c_ott, c_qua, c_fin = st.columns(4)
        with c_sed:
            st.info("Sedicesimi")
            v_s1 = bracket_match(ranks["A"][1], ranks["C"][1], "S1", "Match 1")
            v_s2 = bracket_match(ranks["D"][0], "3rd Group", "S2", "Match 2")
        with c_ott:
            st.info("Ottavi")
            v_o1 = bracket_match(v_s1, v_s2, "O1", "Ottavo 1")
        with c_qua:
            st.info("Quarti")
            v_q1 = bracket_match(v_o1, "Vinc. O2", "Q1", "Quarto 1")
        with c_fin:
            st.info("Fasi Finali")
            v_semi1 = bracket_match(v_q1, "Vinc. Q2", "semi1", "Semi 1")
            st.divider()
            campione = st.selectbox("🏆 SCEGLI IL CAMPIONE", [v_semi1, "Finalista 2"])
            st.session_state["vincitore"] = campione
            if campione != "TBD": st.balloons()

    with tabs[3]: # INVIA
        if st.button("🚀 INVIA PRONOSTICI DEFINITIVAMENTE", use_container_width=True, type="primary"):
            dati = {
                "g": {i: [st.session_state.get(f"h_{i}"), st.session_state.get(f"a_{i}")] for i in range(72)},
                "v": st.session_state.get("vincitore")
            }
            if salva_gspread("Pronostici", user_nick, dati):
                st.success("Pronostici salvati! Buona fortuna!")

    if is_admin: # AREA ADMIN
        with tabs[-1]:
            st.header("👑 Dashboard Admin")
            st.subheader("Classifica Partecipanti")
            # Simulazione classifica (qui andrebbe la logica di lettura gspread)
            st.dataframe(pd.DataFrame({"User": ["Luca", "Marco"], "Punti": [120, 95]}), use_container_width=True)
            
            st.divider()
            if st.button("🪄 TEST: Compila Risultati Reali Admin"):
                for i in range(72):
                    st.session_state[f"adm_h_{i}"] = random.randint(0, 3)
                    st.session_state[f"adm_a_{i}"] = random.randint(0, 3)
                st.rerun()
