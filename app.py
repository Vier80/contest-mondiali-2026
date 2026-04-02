import streamlit as st
import pandas as pd
import json
import gspread
import random
from google.oauth2.service_account import Credentials

# --- 1. CONFIGURAZIONE E STILE LIGHT ---
st.set_page_config(page_title="WC 2026 Contest", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #ffffff; color: #1a1a1a; }
    
    /* Nickname centrato e stretto */
    .nick-container { display: flex; justify-content: center; margin-bottom: 20px; }
    .nick-box { width: 300px; }

    /* Tab grandi e leggibili */
    button[data-baseweb="tab"] p { font-size: 18px !important; font-weight: 700 !important; color: #4b5563 !important; }
    
    /* Card Partite Bianche */
    .stElementContainer div[data-testid="stVerticalBlockBorderControl"] {
        background-color: #f9fafb !important; border: 1px solid #e5e7eb !important; 
        border-radius: 12px !important; padding: 15px !important;
    }

    /* Input numeri grandi */
    input[type="number"] {
        background-color: #ffffff !important; color: #111827 !important;
        font-size: 22px !important; font-weight: 800 !important; border: 2px solid #d1d5db !important;
        text-align: center !important;
    }

    .pts-badge { background: #eff6ff; color: #1e40af; padding: 3px 8px; border-radius: 5px; font-size: 11px; font-weight: 700; border: 1px solid #bfdbfe; }
    .bonus-txt { color: #dc2626; font-size: 10px; font-weight: 800; display: block; margin-top: 5px; }
</style>
""", unsafe_allow_html=True)

# --- 2. DATI RANKING (Dal tuo PDF) ---
RANKING = {
    "Spagna": 1, "Argentina": 2, "Francia": 3, "Inghilterra": 4, "Brasile": 5, "Portogallo": 6, "Olanda": 7, "Belgio": 8,
    "Germania": 9, "Croazia": 10, "Marocco": 11, "Colombia": 13, "Italia": 13, "USA": 14, "Messico": 15, "Uruguay": 16,
    "Svizzera": 17, "Giappone": 18, "Senegal": 19, "Iran": 20, "Sudcorea": 22, "Ecuador": 23, "Austria": 24, "Turchia": 25,
    "Australia": 26, "Canada": 27, "Norvegia": 29, "Panama": 30, "Egitto": 34, "Algeria": 35, "Scozia": 36, "Paraguay": 39,
    "Tunisia": 40, "Costa D'Avorio": 42, "Svezia": 43, "Repubblica Ceca": 44, "Uzbekistan": 50, "DR Congo": 56, "Qatar": 58,
    "Iraq": 58, "Arabia Saudita": 60, "Sudafrica": 61, "Giordania": 66, "Capo Verde": 68, "Bosnia Erzegovina": 71, "Ghana": 72,
    "Curacao": 82, "Haiti": 84, "Nuova Zelanda": 86
}

def get_static_groups():
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

G_TEAMS, MATCHES = get_static_groups()

def get_flag(t):
    if not t or t in ["???", "TBD"]: return "https://flagcdn.com/w160/un.png"
    m = {"Messico": "mx", "Sudafrica": "za", "Sudcorea": "kr", "Repubblica Ceca": "cz", "Canada": "ca", "Bosnia Erzegovina": "ba", "Qatar": "qa", "Svizzera": "ch", "Brasile": "br", "Marocco": "ma", "Haiti": "ht", "Scozia": "gb-sct", "USA": "us", "Paraguay": "py", "Australia": "au", "Turchia": "tr", "Germania": "de", "Curacao": "cw", "Costa D'Avorio": "ci", "Ecuador": "ec", "Olanda": "nl", "Giappone": "jp", "Svezia": "se", "Tunisia": "tn", "Belgio": "be", "Egitto": "eg", "Iran": "ir", "Nuova Zelanda": "nz", "Spagna": "es", "Capo Verde": "cv", "Arabia Saudita": "sa", "Uruguay": "uy", "Francia": "fr", "Senegal": "sn", "Iraq": "iq", "Norvegia": "no", "Argentina": "ar", "Algeria": "dz", "Austria": "at", "Giordania": "jo", "Portogallo": "pt", "DR Congo": "cd", "Uzbekistan": "uz", "Colombia": "co", "Inghilterra": "gb-eng", "Croazia": "hr", "Ghana": "gh", "Panama": "pa", "Italia": "it"}
    return f"https://flagcdn.com/w160/{m.get(t, 'un')}.png"

# --- 3. LOGICA GOOGLE SHEETS ---
def salva_dati(tab, nick, payload):
    try:
        conf = json.loads(st.secrets["service_account"])
        creds = Credentials.from_service_account_info(conf, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
        gc = gspread.authorize(creds)
        # --- CAMBIA IL LINK SOTTO CON IL TUO ---
        URL = "https://docs.google.com/spreadsheets/d/1palUSBw4IlBFzU4dKtgT0tnjPiPEtxIc6K-DK05vXG8/edit?gid=0#gid=0"
        sh = gc.open_by_url(URL)
        ws = sh.worksheet(tab) if tab in [w.title for w in sh.worksheets()] else sh.get_worksheet(0)
        ws.append_row([nick, json.dumps(payload)])
        return True
    except Exception as e:
        st.error(f"❌ ERRORE: {e}")
        st.info(f"Assicurati di aver condiviso il foglio con: {conf['client_email']}")
        return False

# --- 4. CALCOLO CLASSIFICHE ---
def update_standings(pref=""):
    groups = G_TEAMS
    standings = {g: {t: {"Pt": 0, "DR": 0, "GF": 0} for t in ts} for g, ts in groups.items()}
    for i, m in enumerate(MATCHES):
        h = st.session_state.get(f"{pref}h_{i}", 0)
        a = st.session_state.get(f"{pref}a_{i}", 0)
        sh, sa = standings[m['gr']][m['h']], standings[m['gr']][m['a']]
        sh["GF"] += h; sa["GF"] += a; sh["DR"] += (h - a); sa["DR"] += (a - h)
        if h > a: sh["Pt"] += 3
        elif a > h: sa["Pt"] += 3
        else: sh["Pt"] += 1; sa["Pt"] += 1
    
    ranks = {}
    thirds = []
    for g, ts in standings.items():
        df = pd.DataFrame(ts).T.sort_values(["Pt", "DR", "GF"], ascending=False)
        ranks[g] = df.index.tolist()
        thirds.append({"t": df.index[2], "Pt": df.iloc[2]["Pt"], "DR": df.iloc[2]["DR"], "gr": g})
    
    best_3 = pd.DataFrame(thirds).sort_values(["Pt", "DR"], ascending=False).head(8)
    return ranks, best_3, standings

# --- 5. INTERFACCIA ---
st.markdown("<h1 style='text-align: center; color: #1e3a8a;'>WC 2026 Prediction Contest</h1>", unsafe_allow_html=True)

# Nickname centrato
st.markdown("<div class='nick-container'>", unsafe_allow_html=True)
user_name = st.text_input("Inserisci il tuo Nickname:", placeholder="Es. Marco88", key="main_nick")
st.markdown("</div>", unsafe_allow_html=True)

# Login Admin top right
with st.sidebar:
    st.write("### 🔑 Admin")
    pw = st.text_input("Password", type="password")
    is_admin = (pw == "mondiali2026")

if user_name:
    t_labels = ["🌍 Gironi", "📊 Classifiche", "⚔️ Bracket", "🚀 Invia"]
    if is_admin: t_labels.append("👑 Admin Panel")
    tabs = st.tabs(t_labels)

    # --- GIRONI ---
    with tabs[0]:
        if st.button("🪄 Autocompilazione (Mostra Risultati)"):
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
                    p1, p2 = RANKING[m['h']], RANKING[m['a']]
                    px = (p1 + p2) // 2
                    with cols[c]:
                        with st.container(border=True):
                            st.markdown(f"<div style='display:flex; justify-content:space-around;'><span class='pts-badge'>1: {p1}</span><span class='pts-badge'>X: {px}</span><span class='pts-badge'>2: {p2}</span></div>", unsafe_allow_html=True)
                            st.markdown("<span class='bonus-txt'>🎯 +50 pt Risultato Esatto</span>", unsafe_allow_html=True)
                            c1, in1, vs, in2, c2 = st.columns([1, 1.2, 0.4, 1.2, 1])
                            c1.image(get_flag(m['h']), width=30)
                            # Collegamento diretto a session_state per aggiornamento immediato
                            st.session_state[f"h_{idx}"] = in1.number_input("H", 0, 9, key=f"widget_h_{idx}", value=st.session_state.get(f"h_{idx}", 0), label_visibility="collapsed")
                            vs.markdown("<p style='text-align:center; padding-top:8px;'>–</p>", unsafe_allow_html=True)
                            st.session_state[f"a_{idx}"] = in2.number_input("A", 0, 9, key=f"widget_a_{idx}", value=st.session_state.get(f"a_{idx}", 0), label_visibility="collapsed")
                            c2.image(get_flag(m['a']), width=30)
                            st.markdown(f"<p style='text-align:center; font-size:13px; font-weight:700;'>{m['h']} vs {m['a']}</p>", unsafe_allow_html=True)

    # --- BRACKET WIMBLEDON STYLE ---
    def render_bracket(pref=""):
        r, t3, _ = update_standings(pref)
        th_dict = {row['gr']: row['t'] for _, row in t3.iterrows()}
        
        def b_box(t1, t2, mid, lbl):
            with st.container(border=True):
                st.caption(lbl)
                l1, r1 = st.columns(2)
                with l1:
                    st.image(get_flag(t1), width=35)
                    if st.button(f"{t1}", key=f"bt1_{pref}{mid}", use_container_width=True, type="primary" if st.session_state.get(pref+mid)==t1 else "secondary"):
                        st.session_state[pref+mid]=t1; st.rerun()
                with r1:
                    st.image(get_flag(t2), width=35)
                    if st.button(f"{t2}", key=f"bt2_{pref}{mid}", use_container_width=True, type="primary" if st.session_state.get(pref+mid)==t2 else "secondary"):
                        st.session_state[pref+mid]=t2; st.rerun()
                return st.session_state.get(pref+mid, "TBD")

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.write("**Sedicesimi**")
            v1 = b_box(r["A"][1], r["C"][1], "S1", "M1")
            v2 = b_box(r["D"][0], th_dict.get("A", "TBD"), "S2", "M2")
        with c2:
            st.write("**Ottavi**")
            v_o1 = b_box(v1, v2, "O1", "Ottavo 1")
        with c3:
            st.write("**Quarti**")
            v_q1 = b_box(v_o1, "TBD", "Q1", "Quarto 1")
        with c4:
            st.write("**Finali**")
            v_semi = b_box(v_q1, "TBD", "semi", "Semi 1")
            st.divider()
            win = b_box(v_semi, "TBD", "winner", "🏆 CAMPIONE")
            st.session_state[pref+"win_final"] = win
            if win != "TBD" and pref=="": st.balloons()

    with tabs[2]:
        if st.button("🪄 Autocompila Bracket (Test Grafico)"):
            all_teams = list(RANKING.keys())
            for k in ["S1","S2","O1","semi","winner"]: st.session_state[k] = random.choice(all_teams)
            st.rerun()
        render_bracket(pref="")

    # --- ADMIN AREA ---
    if is_admin:
        with tabs[-1]:
            st.header("👑 Admin Panel")
            adm_tab1, adm_tab2 = st.tabs(["📊 Classifica Partecipanti", "⚙️ Inserimento Risultati"])
            
            with adm_tab1:
                st.write("### 🏆 Classifica Generale")
                # Qui si leggerà dal foglio Google "Pronostici"
                mock_rank = pd.DataFrame([{"Utente": "User1", "Punti": 150}, {"Utente": "User2", "Punti": 125}])
                st.table(mock_rank)

            with adm_tab2:
                if st.button("🪄 Popola Risultati Reali (Random)"):
                    for i in range(72):
                        st.session_state[f"adm_h_{i}"] = random.randint(0, 3)
                        st.session_state[f"adm_a_{i}"] = random.randint(0, 3)
                    st.rerun()
                for i, m in enumerate(MATCHES):
                    with st.expander(f"{m['h']} vs {m['a']}"):
                        ca1, ca2 = st.columns(2)
                        st.session_state[f"adm_h_{i}"] = ca1.number_input("H", 0, 9, key=f"ah_re_{i}", value=st.session_state.get(f"adm_h_{i}", 0))
                        st.session_state[f"adm_a_{i}"] = ca2.number_input("A", 0, 9, key=f"aa_re_{i}", value=st.session_state.get(f"adm_a_{i}", 0))
                st.write("### ⚔️ Bracket Reale")
                render_bracket(pref="adm_")

    with tabs[3]:
        if st.button("🚀 INVIA PRONOSTICI DEFINITIVAMENTE", type="primary", use_container_width=True):
            user_payload = {i: [st.session_state.get(f"h_{i}"), st.session_state.get(f"a_{i}")] for i in range(72)}
            if salva_dati("Pronostici", user_name, {"g": user_payload, "v": st.session_state.get("win_final")}):
                st.success("Pronostici inviati!")
