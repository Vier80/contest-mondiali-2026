import streamlit as st
import pandas as pd
import json
import gspread
import random
from google.oauth2.service_account import Credentials

# --- 1. CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="WC 2026 - Master Contest", layout="wide")

# CSS: DESIGN PREMIUM DARK
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap');
    .stApp { background-color: #0f172a; color: #f8fafc; font-family: 'Inter', sans-serif; }
    
    /* Titoli e Tab */
    h1, h2, h3 { color: #38bdf8 !important; font-weight: 900 !important; }
    button[data-baseweb="tab"] p { font-size: 22px !important; font-weight: 800 !important; }
    
    /* Card Partite */
    .match-card {
        background: #1e293b; border-radius: 12px; padding: 15px; 
        border: 1px solid #334155; margin-bottom: 10px;
    }
    
    /* Punti 1X2 */
    .ranking-info {
        background: #0369a1; color: #e0f2fe; border-radius: 6px; 
        font-size: 13px; font-weight: 800; padding: 5px; text-align: center; margin-bottom: 10px;
    }

    /* Input Numerici */
    input[type="number"] {
        background-color: #334155 !important; color: #ffffff !important;
        font-size: 22px !important; font-weight: 900 !important; 
        border: 2px solid #38bdf8 !important; border-radius: 8px !important;
    }
    
    .team-name-label { font-size: 14px; font-weight: 700; color: #f1f5f9; text-align: center; }
</style>
""", unsafe_allow_html=True)

# --- 2. DATABASE RANKING (Aggiornato da PDF) ---
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

def get_groups():
    return {
        "A": ["Messico", "Sudafrica", "Sudcorea", "Repubblica Ceca"], "B": ["Canada", "Bosnia Erzegovina", "Qatar", "Svizzera"],
        "C": ["Brasile", "Marocco", "Haiti", "Scozia"], "D": ["USA", "Paraguay", "Australia", "Turchia"],
        "E": ["Germania", "Curacao", "Costa D'Avorio", "Ecuador"], "F": ["Olanda", "Giappone", "Svezia", "Tunisia"],
        "G": ["Belgio", "Egitto", "Iran", "Nuova Zelanda"], "H": ["Spagna", "Capo Verde", "Arabia Saudita", "Uruguay"],
        "I": ["Francia", "Senegal", "Iraq", "Norvegia"], "J": ["Argentina", "Algeria", "Austria", "Giordania"],
        "K": ["Portogallo", "DR Congo", "Uzbekistan", "Colombia"], "L": ["Inghilterra", "Croazia", "Ghana", "Panama"]
    }

def get_matchlist():
    g = get_groups()
    ml = []
    for gid, teams in g.items():
        for h, a in [(0, 1), (2, 3), (0, 2), (1, 3), (0, 3), (1, 2)]:
            ml.append({"gr": gid, "h": teams[h], "a": teams[a]})
    return ml

MATCHES = get_matchlist()

def get_flag(t):
    if not t or t in ["???", "TBD", "Non assegnato"]: return "https://flagcdn.com/w160/un.png"
    m = {"Messico": "mx", "Sudafrica": "za", "Sudcorea": "kr", "Repubblica Ceca": "cz", "Canada": "ca", "Bosnia Erzegovina": "ba", "Qatar": "qa", "Svizzera": "ch", "Brasile": "br", "Marocco": "ma", "Haiti": "ht", "Scozia": "gb-sct", "USA": "us", "Paraguay": "py", "Australia": "au", "Turchia": "tr", "Germania": "de", "Curacao": "cw", "Costa D'Avorio": "ci", "Ecuador": "ec", "Olanda": "nl", "Giappone": "jp", "Svezia": "se", "Tunisia": "tn", "Belgio": "be", "Egitto": "eg", "Iran": "ir", "Nuova Zelanda": "nz", "Spagna": "es", "Capo Verde": "cv", "Arabia Saudita": "sa", "Uruguay": "uy", "Francia": "fr", "Senegal": "sn", "Iraq": "iq", "Norvegia": "no", "Argentina": "ar", "Algeria": "dz", "Austria": "at", "Giordania": "jo", "Portogallo": "pt", "DR Congo": "cd", "Uzbekistan": "uz", "Colombia": "co", "Inghilterra": "gb-eng", "Croazia": "hr", "Ghana": "gh", "Panama": "pa", "Italia": "it"}
    return f"https://flagcdn.com/w160/{m.get(t, 'un')}.png"

# --- 3. GOOGLE SHEETS & ADMIN LOGIC ---
def get_gspread_client():
    info = json.loads(st.secrets["service_account"])
    creds = Credentials.from_service_account_info(info, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
    return gspread.authorize(creds), info['client_email']

def salva_dati(tab, nick, payload):
    try:
        client, email = get_gspread_client()
        URL = "https://docs.google.com/spreadsheets/d/1palUSBw4IlBFzU4dKtgT0tnjPiPEtxIc6K-DK05vXG8/edit?gid=0#gid=0" # <--- METTI IL LINK DEL TUO FOGLIO
        sh = client.open_by_url(URL)
        try: ws = sh.worksheet(tab)
        except: ws = sh.get_worksheet(0)
        ws.append_row([nick, json.dumps(payload)])
        return True
    except Exception as e:
        st.error(f"Errore 403: Devi condividere il foglio con l'email: {email}")
        return False

# --- 4. INTERFACCIA ---
col_logo, col_login = st.columns([7, 3])
with col_logo:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/a/a7/2026_FIFA_World_Cup_logo.svg/512px-2026_FIFA_World_Cup_logo.svg.png", width=120)
with col_login:
    st.write("### 🔐 Admin")
    adm_pw = st.text_input("Password", type="password", label_visibility="collapsed")
    is_admin = (adm_pw == "mondiali2026")

user_nick = st.text_input("👤 Nickname Partecipante:", placeholder="Scrivi il tuo nome...")

if user_nick:
    tab_labels = ["🏟️ Gironi", "📊 Classifiche", "⚔️ Bracket", "🚀 Invia"]
    if is_admin: tab_labels.append("👑 Admin Panel")
    tabs = st.tabs(tab_labels)

    # --- GIRONI ---
    with tabs[0]:
        st.write("### Compila i tuoi pronostici")
        if st.button("🪄 Autocompila Gironi (Random)"):
            for i in range(len(MATCHES)):
                st.session_state[f"h_{i}"] = random.randint(0, 4)
                st.session_state[f"a_{i}"] = random.randint(0, 4)
            st.rerun()

        for r in range(18):
            cols = st.columns(4)
            for c in range(4):
                idx = r * 4 + c
                if idx < 72:
                    m = MATCHES[idx]
                    pts_1, pts_2 = RANKING[m['a']], RANKING[m['h']]
                    pts_x = (pts_1 + pts_2) // 2
                    with cols[c]:
                        with st.container(border=True):
                            st.markdown(f"<div class='ranking-info'>1: {pts_1} | X: {pts_x} | 2: {pts_2}</div>", unsafe_allow_html=True)
                            sc_col = st.columns([1, 1.2, 0.4, 1.2, 1])
                            sc_col[0].image(get_flag(m['h']), width=30)
                            st.session_state[f"h_{idx}"] = sc_col[1].number_input("H", 0, 9, key=f"in_h_{idx}", value=st.session_state.get(f"h_{idx}", 0), label_visibility="collapsed")
                            sc_col[2].markdown("<p style='text-align:center; padding-top:8px;'>–</p>", unsafe_allow_html=True)
                            st.session_state[f"a_{idx}"] = sc_col[3].number_input("A", 0, 9, key=f"in_a_{idx}", value=st.session_state.get(f"a_{idx}", 0), label_visibility="collapsed")
                            sc_col[4].image(get_flag(m['a']), width=30)
                            st.markdown(f"<p class='team-name-label'>{m['h']} vs {m['a']}</p>", unsafe_allow_html=True)

    # --- CLASSIFICHE ---
    with tabs[1]:
        st.write("### Situazione Gironi")
        stats = {g: {t: {"Pt": 0, "DR": 0} for t in ts} for g, ts in get_groups().items()}
        for i, m in enumerate(MATCHES):
            h, a = st.session_state.get(f"h_{i}", 0), st.session_state.get(f"a_{i}", 0)
            sh, sa = stats[m['gr']][m['h']], stats[m['gr']][m['a']]
            sh["DR"] += (h - a); sa["DR"] += (a - h)
            if h > a: sh["Pt"] += 3
            elif a > h: sa["Pt"] += 3
            else: sh["Pt"] += 1; sa["Pt"] += 1
        
        ranks = {g: pd.DataFrame(ts).T.sort_values(["Pt", "DR"], ascending=False) for g, ts in stats.items()}
        for i in range(0, 12, 3):
            cols = st.columns(3)
            for k in range(3):
                gid = list(get_groups().keys())[i+k]
                cols[k].write(f"**Gruppo {gid}**")
                cols[k].dataframe(ranks[gid], use_container_width=True)

    # --- BRACKET TENNISTICO ---
    with tabs[2]:
        st.write("### ⚔️ Tabellone Eliminazione Diretta")
        if st.button("🪄 Autocompila Bracket (Test)"):
            all_teams = list(RANKING.keys())
            for key in ["S1","S2","S3","S4","O1","O2","Q1","semi1","winner"]:
                st.session_state[key] = random.choice(all_teams)
            st.rerun()

        def render_b(t1, t2, mid, lbl):
            with st.container(border=True):
                st.caption(lbl)
                c1, c2 = st.columns(2)
                with c1:
                    st.image(get_flag(t1), width=35)
                    if st.button(f"{t1}", key=f"btn1_{mid}", use_container_width=True, type="primary" if st.session_state.get(mid)==t1 else "secondary"):
                        st.session_state[mid]=t1; st.rerun()
                with c2:
                    st.image(get_flag(t2), width=35)
                    if st.button(f"{t2}", key=f"btn2_{mid}", use_container_width=True, type="primary" if st.session_state.get(mid)==t2 else "secondary"):
                        st.session_state[mid]=t2; st.rerun()
                return st.session_state.get(mid, "TBD")

        # Layout Orizzontale
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.info("Sedicesimi")
            v_s1 = render_b("TBD", "TBD", "S1", "M1")
            v_s2 = render_b("TBD", "TBD", "S2", "M2")
        with c2:
            st.info("Ottavi")
            v_o1 = render_b(v_s1, v_s2, "O1", "Ottavo 1")
        with c3:
            st.info("Quarti")
            v_q1 = render_compact_match := render_b(v_o1, "TBD", "Q1", "Quarto 1")
        with c4:
            st.info("Fasi Finali")
            v_semi1 = render_b(v_q1, "TBD", "semi1", "Semi 1")
            st.divider()
            winner = render_b(v_semi1, "TBD", "winner", "🏆 CAMPIONE")
            st.session_state["vincitore_finale"] = winner
            if winner != "TBD": st.balloons()

    # --- ADMIN ---
    if is_admin:
        with tabs[-1]:
            st.header("👑 Dashboard Admin")
            if st.button("🪄 Auto-compila Risultati Reali"):
                for i in range(72):
                    st.session_state[f"adm_h_{i}"] = random.randint(0, 3)
                    st.session_state[f"adm_a_{i}"] = random.randint(0, 3)
                st.rerun()
            
            st.subheader("Inserisci Risultati Ufficiali")
            for i, m in enumerate(MATCHES):
                with st.expander(f"{m['h']} vs {m['a']}"):
                    ca1, ca2 = st.columns(2)
                    st.session_state[f"adm_h_{i}"] = ca1.number_input("H", 0, 9, key=f"ah_{i}", value=st.session_state.get(f"adm_h_{i}", 0))
                    st.session_state[f"adm_a_{i}"] = ca2.number_input("A", 0, 9, key=f"aa_{i}", value=st.session_state.get(f"adm_a_{i}", 0))
            
            if st.button("💾 SALVA RISULTATI UFFICIALI"):
                adm_data = {i: [st.session_state.get(f"adm_h_{i}"), st.session_state.get(f"adm_a_{i}")] for i in range(72)}
                salva_dati("RisultatiReali", "OFFICIAL", adm_data)

    # --- INVIO ---
    with tabs[3]:
        if st.button("🚀 INVIA PRONOSTICI DEFINITIVAMENTE", type="primary", use_container_width=True):
            g_payload = {i: [st.session_state.get(f"h_{i}"), st.session_state.get(f"a_{i}")] for i in range(72)}
            if salva_dati("Pronostici", user_nick, {"g": g_payload, "v": st.session_state.get("vincitore_finale")}):
                st.success("Dati inviati correttamente al Database!")
