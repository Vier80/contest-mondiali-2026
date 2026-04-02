import streamlit as st
import pandas as pd
import json
import gspread
import random
from google.oauth2.service_account import Credentials

# --- 1. CONFIGURAZIONE E STILE ---
st.set_page_config(page_title="WC 2026 PRO", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    .stApp { background-color: #0f172a; color: #f1f5f9; font-family: 'Inter', sans-serif; }
    
    /* TAB GRANDI E MORBIDI */
    button[data-baseweb="tab"] { height: 60px !important; }
    button[data-baseweb="tab"] p { font-size: 18px !important; font-weight: 600 !important; color: #94a3b8 !important; }
    button[data-baseweb="tab"][aria-selected="true"] p { color: #38bdf8 !important; }

    /* CARD DESIGN */
    .stElementContainer div[data-testid="stVerticalBlockBorderControl"] {
        background-color: #1e293b !important; border: 1px solid #334155 !important; border-radius: 12px !important;
    }
    
    /* INPUT STYLE */
    input[type="number"] {
        background-color: #0f172a !important; color: #38bdf8 !important;
        font-size: 20px !important; font-weight: 800 !important; border: 1px solid #334155 !important;
    }
    
    .ranking-tag { background: #075985; color: #e0f2fe; padding: 3px 8px; border-radius: 4px; font-size: 11px; font-weight: 700; }
</style>
""", unsafe_allow_html=True)

# --- 2. DATABASE RANKING E SQUADRE ---
RANKING = {
    "Messico": 15, "Sudafrica": 61, "Sudcorea": 22, "Repubblica Ceca": 44, "Canada": 27, "Bosnia Erzegovina": 71, "Qatar": 58, "Svizzera": 17,
    "Brasile": 5, "Marocco": 11, "Haiti": 84, "Scozia": 36, "USA": 14, "Paraguay": 39, "Australia": 26, "Turchia": 25, "Germania": 9, "Curacao": 82,
    "Costa D'Avorio": 42, "Ecuador": 23, "Olanda": 7, "Giappone": 18, "Svezia": 43, "Tunisia": 40, "Belgio": 8, "Egitto": 34, "Iran": 20, 
    "Nuova Zelanda": 86, "Spagna": 1, "Capo Verde": 68, "Arabia Saudita": 60, "Uruguay": 16, "Francia": 3, "Senegal": 19, "Iraq": 58, 
    "Norvegia": 29, "Argentina": 2, "Algeria": 35, "Austria": 24, "Giordania": 66, "Portogallo": 6, "DR Congo": 56, "Uzbekistan": 50, 
    "Colombia": 13, "Inghilterra": 4, "Croazia": 10, "Ghana": 72, "Panama": 30, "Italia": 13
}

def get_static_data():
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

G_TEAMS, MATCHES = get_static_data()

def get_flag(t):
    if not t or t in ["???", "TBD"]: return "https://flagcdn.com/w160/un.png"
    m = {"Messico": "mx", "Sudafrica": "za", "Sudcorea": "kr", "Repubblica Ceca": "cz", "Canada": "ca", "Bosnia Erzegovina": "ba", "Qatar": "qa", "Svizzera": "ch", "Brasile": "br", "Marocco": "ma", "Haiti": "ht", "Scozia": "gb-sct", "USA": "us", "Paraguay": "py", "Australia": "au", "Turchia": "tr", "Germania": "de", "Curacao": "cw", "Costa D'Avorio": "ci", "Ecuador": "ec", "Olanda": "nl", "Giappone": "jp", "Svezia": "se", "Tunisia": "tn", "Belgio": "be", "Egitto": "eg", "Iran": "ir", "Nuova Zelanda": "nz", "Spagna": "es", "Capo Verde": "cv", "Arabia Saudita": "sa", "Uruguay": "uy", "Francia": "fr", "Senegal": "sn", "Iraq": "iq", "Norvegia": "no", "Argentina": "ar", "Algeria": "dz", "Austria": "at", "Giordania": "jo", "Portogallo": "pt", "DR Congo": "cd", "Uzbekistan": "uz", "Colombia": "co", "Inghilterra": "gb-eng", "Croazia": "hr", "Ghana": "gh", "Panama": "pa", "Italia": "it"}
    return f"https://flagcdn.com/w160/{m.get(t, 'un')}.png"

# --- 3. GOOGLE SHEETS CORE ---
def invia_dati(tab, nick, data):
    try:
        conf = json.loads(st.secrets["service_account"])
        creds = Credentials.from_service_account_info(conf, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
        gc = gspread.authorize(creds)
        # INSERISCI IL TUO URL QUI
        URL = "https://docs.google.com/spreadsheets/d/1palUSBw4IlBFzU4dKtgT0tnjPiPEtxIc6K-DK05vXG8/edit?gid=0#gid=0"
        sh = gc.open_by_url(URL)
        ws = sh.worksheet(tab) if tab in [w.title for w in sh.worksheets()] else sh.get_worksheet(0)
        ws.append_row([nick, json.dumps(data)])
        return True
    except Exception as e:
        st.error(f"⚠️ ERRORE INVIO: {e}")
        st.error(f"Copia questa email e aggiungila come EDITOR sul tuo foglio Google: {conf['client_email']}")
        return False

# --- 4. LOGICA CALCOLO ---
def process_standings(pref=""):
    results = {g: {t: {"Pt": 0, "DR": 0, "GF": 0} for t in ts} for g, ts in G_TEAMS.items()}
    for i, m in enumerate(MATCHES):
        h = st.session_state.get(f"{pref}h_{i}", 0)
        a = st.session_state.get(f"{pref}a_{i}", 0)
        sh, sa = results[m['gr']][m['h']], results[m['gr']][m['a']]
        sh["GF"] += h; sa["GF"] += a; sh["DR"] += (h - a); sa["DR"] += (a - h)
        if h > a: sh["Pt"] += 3
        elif a > h: sa["Pt"] += 3
        else: sh["Pt"] += 1; sa["Pt"] += 1
    
    ranks = {}
    thirds = []
    for g, ts in results.items():
        df = pd.DataFrame(ts).T.sort_values(["Pt", "DR", "GF"], ascending=False)
        ranks[g] = df.index.tolist()
        thirds.append({"t": df.index[2], "Pt": df.iloc[2]["Pt"], "DR": df.iloc[2]["DR"], "gr": g})
    
    best_3 = pd.DataFrame(thirds).sort_values(["Pt", "DR"], ascending=False).head(8)
    return ranks, best_3, results

# --- 5. INTERFACCIA ---
st.columns([1, 5, 1])[1].image("https://upload.wikimedia.org/wikipedia/commons/thumb/a/a7/2026_FIFA_World_Cup_logo.svg/512px-2026_FIFA_World_Cup_logo.svg.png", width=120)

# LOGIN ADMIN NASCOSTO
with st.sidebar:
    adm_code = st.text_input("🔑 Admin Mode", type="password")
    is_admin = (adm_code == "mondiali2026")

user = st.text_input("👤 Inserisci il tuo Nickname:", placeholder="Es. Luca_2026")

if user:
    tabs = st.tabs(["🌍 Gironi", "📊 Classifiche", "⚔️ Bracket", "🚀 Salva"] + (["👑 Admin"] if is_admin else []))

    # --- TAB GIRONI ---
    with tabs[0]:
        if st.button("🪄 Compilazione Random"):
            for i in range(72):
                st.session_state[f"h_{i}"] = random.randint(0, 3)
                st.session_state[f"a_{i}"] = random.randint(0, 3)
            st.rerun()
            
        for r in range(18):
            cols = st.columns(4)
            for c in range(4):
                idx = r * 4 + c
                if idx < 72:
                    m = MATCHES[idx]
                    p1, p2 = RANKING[m['a']], RANKING[m['h']]
                    with cols[c]:
                        with st.container(border=True):
                            st.markdown(f"<span class='ranking-tag'>Punti 1: {p1} | X: {(p1+p2)//2} | 2: {p2}</span>", unsafe_allow_html=True)
                            c1, c_in1, c_vs, c_in2, c2 = st.columns([1, 1.2, 0.4, 1.2, 1])
                            c1.image(get_flag(m['h']), width=30)
                            st.session_state[f"h_{idx}"] = c_in1.number_input("H", 0, 9, key=f"nh_{idx}", value=st.session_state.get(f"h_{idx}", 0), label_visibility="collapsed")
                            c_vs.markdown("<p style='text-align:center; padding-top:8px;'>–</p>", unsafe_allow_html=True)
                            st.session_state[f"a_{idx}"] = c_in2.number_input("A", 0, 9, key=f"na_{idx}", value=st.session_state.get(f"a_{idx}", 0), label_visibility="collapsed")
                            c2.image(get_flag(m['a']), width=30)
                            st.markdown(f"<p style='text-align:center; font-size:12px; font-weight:700;'>{m['h']} vs {m['a']}</p>", unsafe_allow_html=True)

    # --- TAB BRACKET (TENNISTICO SX-DX) ---
    def generate_bracket_ui(prefix=""):
        r, t3_df, _ = process_standings(prefix)
        th_dict = {row['gr']: row['t'] for _, row in t3_df.iterrows()}
        
        def match_box(t1, t2, mid, label):
            with st.container(border=True):
                st.caption(label)
                col1, col2 = st.columns(2)
                with col1:
                    st.image(get_flag(t1), width=40)
                    if st.button(f"{t1}", key=f"b1_{prefix}_{mid}", use_container_width=True, type="primary" if st.session_state.get(prefix+mid) == t1 else "secondary"):
                        st.session_state[prefix+mid] = t1; st.rerun()
                with col2:
                    st.image(get_flag(t2), width=40)
                    if st.button(f"{t2}", key=f"b2_{prefix}_{mid}", use_container_width=True, type="primary" if st.session_state.get(prefix+mid) == t2 else "secondary"):
                        st.session_state[prefix+mid] = t2; st.rerun()
                return st.session_state.get(prefix+mid, "TBD")

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.write("📌 Sedicesimi")
            v_s1 = match_box(r["A"][1], r["C"][1], "S1", "M1")
            v_s2 = match_box(r["D"][0], th_dict.get("A", "TBD"), "S2", "M2")
        with c2:
            st.write("🎯 Ottavi")
            v_o1 = match_box(v_s1, v_s2, "O1", "Ottavo 1")
        with c3:
            st.write("💎 Quarti")
            v_q1 = match_box(v_o1, "TBD", "Q1", "Quarto 1")
        with c4:
            st.write("🏆 Finale")
            v_semi1 = match_box(v_q1, "TBD", "semi1", "Semi 1")
            st.divider()
            win = match_box(v_semi1, "TBD", "winner", "CAMPIONE")
            st.session_state[prefix+"vincitore_finale"] = win
            if win != "TBD" and prefix=="": st.balloons()

    with tabs[2]:
        st.subheader("⚔️ Tabellone Eliminazione Diretta")
        generate_bracket_ui(prefix="")

    # --- TAB ADMIN (GESTIONE RISULTATI REALI) ---
    if is_admin:
        with tabs[-1]:
            st.header("👑 Pannello Admin")
            col_a1, col_a2 = st.columns(2)
            if col_a1.button("🪄 Auto-compila Risultati REALI (Test)"):
                for i in range(72):
                    st.session_state[f"adm_h_{i}"] = random.randint(0, 3)
                    st.session_state[f"adm_a_{i}"] = random.randint(0, 3)
                st.rerun()
            
            st.write("### 🏟️ Inserisci Risultati Ufficiali")
            for i, m in enumerate(MATCHES):
                with st.expander(f"{m['h']} vs {m['a']}"):
                    ca1, ca2 = st.columns(2)
                    st.session_state[f"adm_h_{i}"] = ca1.number_input("H", 0, 9, key=f"ah_re_{i}", value=st.session_state.get(f"adm_h_{i}", 0))
                    st.session_state[f"adm_a_{i}"] = ca2.number_input("A", 0, 9, key=f"aa_re_{i}", value=st.session_state.get(f"adm_a_{i}", 0))
            
            st.divider()
            st.write("### ⚔️ Bracket Reale (Generato dai tuoi dati Admin)")
            generate_bracket_ui(prefix="adm_")
            
            if st.button("💾 SALVA RISULTATI UFFICIALI"):
                adm_data = {i: [st.session_state.get(f"adm_h_{i}"), st.session_state.get(f"adm_a_{i}")] for i in range(72)}
                invia_dati("RisultatiReali", "ADMIN_OFFICIAL", adm_data)

    # --- TAB INVIO ---
    with tabs[3]:
        if st.button("🚀 INVIA PRONOSTICI DEFINITIVAMENTE", type="primary", use_container_width=True):
            user_payload = {i: [st.session_state.get(f"h_{i}"), st.session_state.get(f"a_{i}")] for i in range(72)}
            if invia_dati("Pronostici", user, {"g": user_payload, "v": st.session_state.get("vincitore_finale")}):
                st.success("Pronostici salvati! Buona fortuna!")
