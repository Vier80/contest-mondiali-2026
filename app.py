import streamlit as st
import pandas as pd
import json
import gspread
import random
from google.oauth2.service_account import Credentials

# --- 1. CONFIGURAZIONE PAGINA (LIGHT MODE) ---
st.set_page_config(page_title="FIFA World Cup 2026 Conest", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    
    /* SFONDO CHIARO E RIPOSANTE */
    .stApp { background-color: #f8fafc; color: #1e293b; font-family: 'Inter', sans-serif; }
    
    /* TAB PROFESSIONALI */
    button[data-baseweb="tab"] { height: 60px !important; }
    button[data-baseweb="tab"] p { font-size: 18px !important; font-weight: 700 !important; color: #64748b !important; }
    button[data-baseweb="tab"][aria-selected="true"] p { color: #0284c7 !important; }

    /* CARD BIANCHE PULITE */
    .stElementContainer div[data-testid="stVerticalBlockBorderControl"] {
        background-color: #ffffff !important; border: 1px solid #e2e8f0 !important; 
        border-radius: 12px !important; box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1) !important;
    }
    
    /* INPUT CHIARI */
    input[type="number"] {
        background-color: #f1f5f9 !important; color: #0f172a !important;
        font-size: 22px !important; font-weight: 800 !important; border: 2px solid #e2e8f0 !important;
        border-radius: 8px !important; text-align: center !important;
    }
    
    .ranking-badge { 
        background: #e0f2fe; color: #0369a1; padding: 4px 10px; 
        border-radius: 6px; font-size: 12px; font-weight: 800; border: 1px solid #bae6fd;
    }
    
    .team-label { color: #1e293b; font-weight: 700; font-size: 14px; }
</style>
""", unsafe_allow_html=True)

# --- 2. DATABASE RANKING (DATI PDF) ---
RANKING = {
    "Messico": 15, "Sudafrica": 61, "Sudcorea": 22, "Repubblica Ceca": 44, "Canada": 27, "Bosnia Erzegovina": 71, "Qatar": 58, "Svizzera": 17,
    "Brasile": 5, "Marocco": 11, "Haiti": 84, "Scozia": 36, "USA": 14, "Paraguay": 39, "Australia": 26, "Turchia": 25, "Germania": 9, "Curacao": 82,
    "Costa D'Avorio": 42, "Ecuador": 23, "Olanda": 7, "Giappone": 18, "Svezia": 43, "Tunisia": 40, "Belgio": 8, "Egitto": 34, "Iran": 20, 
    "Nuova Zelanda": 86, "Spagna": 1, "Capo Verde": 68, "Arabia Saudita": 60, "Uruguay": 16, "Francia": 3, "Senegal": 19, "Iraq": 58, 
    "Norvegia": 29, "Argentina": 2, "Algeria": 35, "Austria": 24, "Giordania": 66, "Portogallo": 6, "DR Congo": 56, "Uzbekistan": 50, 
    "Colombia": 13, "Inghilterra": 4, "Croazia": 10, "Ghana": 72, "Panama": 30, "Italia": 13
}

def get_base_data():
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

G_TEAMS, MATCHES = get_base_data()

def get_flag(t):
    if not t or t in ["???", "TBD"]: return "https://flagcdn.com/w160/un.png"
    m = {"Messico": "mx", "Sudafrica": "za", "Sudcorea": "kr", "Repubblica Ceca": "cz", "Canada": "ca", "Bosnia Erzegovina": "ba", "Qatar": "qa", "Svizzera": "ch", "Brasile": "br", "Marocco": "ma", "Haiti": "ht", "Scozia": "gb-sct", "USA": "us", "Paraguay": "py", "Australia": "au", "Turchia": "tr", "Germania": "de", "Curacao": "cw", "Costa D'Avorio": "ci", "Ecuador": "ec", "Olanda": "nl", "Giappone": "jp", "Svezia": "se", "Tunisia": "tn", "Belgio": "be", "Egitto": "eg", "Iran": "ir", "Nuova Zelanda": "nz", "Spagna": "es", "Capo Verde": "cv", "Arabia Saudita": "sa", "Uruguay": "uy", "Francia": "fr", "Senegal": "sn", "Iraq": "iq", "Norvegia": "no", "Argentina": "ar", "Algeria": "dz", "Austria": "at", "Giordania": "jo", "Portogallo": "pt", "DR Congo": "cd", "Uzbekistan": "uz", "Colombia": "co", "Inghilterra": "gb-eng", "Croazia": "hr", "Ghana": "gh", "Panama": "pa", "Italia": "it"}
    return f"https://flagcdn.com/w160/{m.get(t, 'un')}.png"

# --- 3. GOOGLE SHEETS CORE ---
def invia_su_foglio(tab, nick, payload):
    try:
        conf = json.loads(st.secrets["service_account"])
        creds = Credentials.from_service_account_info(conf, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
        gc = gspread.authorize(creds)
        # INSERISCI QUI IL TUO LINK
        URL = "https://docs.google.com/spreadsheets/d/1palUSBw4IlBFzU4dKtgT0tnjPiPEtxIc6K-DK05vXG8/edit?gid=0#gid=0"
        sh = gc.open_by_url(URL)
        ws = sh.worksheet(tab) if tab in [w.title for w in sh.worksheets()] else sh.get_worksheet(0)
        ws.append_row([nick, json.dumps(payload)])
        return True
    except Exception as e:
        st.error(f"❌ ERRORE GOOGLE SHEETS: {e}")
        return False

# --- 4. LOGICA CLASSIFICHE ---
def update_standings(pref=""):
    standings = {g: {t: {"Pt": 0, "DR": 0, "GF": 0} for t in ts} for g, ts in G_TEAMS.items()}
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
st.columns([1, 4, 1])[1].image("https://upload.wikimedia.org/wikipedia/commons/thumb/a/a7/2026_FIFA_World_Cup_logo.svg/512px-2026_FIFA_World_Cup_logo.svg.png", width=140)

with st.sidebar:
    st.write("### 🔒 Area Riservata")
    code = st.text_input("Admin Password", type="password")
    is_admin = (code == "mondiali2026")

user = st.text_input("👤 Nickname:", placeholder="Es. Luca_Contest")

if user:
    tabs = st.tabs(["🌍 Gironi", "📊 Classifiche", "⚔️ Bracket", "🚀 Salva"] + (["👑 Admin"] if is_admin else []))

    # --- TAB GIRONI ---
    with tabs[0]:
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
                    pts_1, pts_2 = RANKING[m['a']], RANKING[m['h']] # Vittoria casa vale rank ospite e viceversa
                    pts_x = (pts_1 + pts_2) // 2
                    with cols[c]:
                        with st.container(border=True):
                            st.markdown(f"<span class='ranking-badge'>Punti: 1={pts_1} | X={pts_x} | 2={pts_2}</span>", unsafe_allow_html=True)
                            c1, in1, vs, in2, c2 = st.columns([1, 1.2, 0.4, 1.2, 1])
                            c1.image(get_flag(m['h']), width=30)
                            # UTILIZZO DEL PARAMETRO VALUE PER MOSTRARE IL RISULTATO
                            st.session_state[f"h_{idx}"] = in1.number_input("H", 0, 9, key=f"nh_{idx}", value=st.session_state.get(f"h_{idx}", 0), label_visibility="collapsed")
                            vs.markdown("<p style='text-align:center; padding-top:8px;'>–</p>", unsafe_allow_html=True)
                            st.session_state[f"a_{idx}"] = in2.number_input("A", 0, 9, key=f"na_{idx}", value=st.session_state.get(f"a_{idx}", 0), label_visibility="collapsed")
                            c2.image(get_flag(m['a']), width=30)
                            st.markdown(f"<p class='team-label' style='text-align:center;'>{m['h']} vs {m['a']}</p>", unsafe_allow_html=True)

    # --- FUNZIONE BRACKET GENERICA (PER UTENTE E ADMIN) ---
    def render_bracket(prefix=""):
        r, t3_df, _ = update_standings(prefix)
        th_dict = {row['gr']: row['t'] for _, row in t3_df.iterrows()}
        
        def b_box(t1, t2, mid, label):
            with st.container(border=True):
                st.caption(label)
                col1, col2 = st.columns(2)
                with col1:
                    st.image(get_flag(t1), width=40)
                    if st.button(f"{t1}", key=f"bt1_{prefix}_{mid}", use_container_width=True, type="primary" if st.session_state.get(prefix+mid) == t1 else "secondary"):
                        st.session_state[prefix+mid] = t1; st.rerun()
                with col2:
                    st.image(get_flag(t2), width=40)
                    if st.button(f"{t2}", key=f"bt2_{prefix}_{mid}", use_container_width=True, type="primary" if st.session_state.get(prefix+mid) == t2 else "secondary"):
                        st.session_state[prefix+mid] = t2; st.rerun()
                return st.session_state.get(prefix+mid, "TBD")

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.write("**Sedicesimi**")
            v_s1 = b_box(r["A"][1], r["C"][1], "S1", "M1")
            v_s2 = b_box(r["D"][0], th_dict.get("A", "TBD"), "S2", "M2")
        with c2:
            st.write("**Ottavi**")
            v_o1 = b_box(v_s1, v_s2, "O1", "Ottavo 1")
        with c3:
            st.write("**Quarti**")
            v_q1 = b_box(v_o1, "TBD", "Q1", "Quarto 1")
        with c4:
            st.write("**Finali**")
            v_semi1 = b_box(v_q1, "TBD", "semi1", "Semi 1")
            st.divider()
            win = b_box(v_semi1, "TBD", "winner", "🏆 CAMPIONE")
            st.session_state[prefix+"vincitore"] = win
            if win != "TBD" and prefix=="": st.balloons()

    with tabs[2]:
        render_bracket(prefix="")

    # --- TAB ADMIN (LOGICA COMPLETA) ---
    if is_admin:
        with tabs[-1]:
            st.header("👑 Admin Panel - Risultati Ufficiali")
            if st.button("🪄 Auto-compila Risultati UFFICIALI (Test Admin)"):
                for i in range(72):
                    st.session_state[f"adm_h_{i}"] = random.randint(0, 3)
                    st.session_state[f"adm_a_{i}"] = random.randint(0, 3)
                st.rerun()
            
            st.subheader("1. Inserisci i Risultati REALI delle 72 Partite")
            for i, m in enumerate(MATCHES):
                with st.expander(f"Girone {m['gr']}: {m['h']} vs {m['a']}"):
                    ca1, ca2 = st.columns(2)
                    # BOX COLLEGATI ALLO STATO PER L'AUTOCOMPILAZIONE
                    st.session_state[f"adm_h_{i}"] = ca1.number_input(f"Casa ({m['h']})", 0, 9, key=f"ah_re_{i}", value=st.session_state.get(f"adm_h_{i}", 0))
                    st.session_state[f"adm_a_{i}"] = ca2.number_input(f"Ospite ({m['a']})", 0, 9, key=f"aa_re_{i}", value=st.session_state.get(f"adm_a_{i}", 0))
            
            st.divider()
            st.subheader("2. Bracket Reale (Generato dai Risultati Admin)")
            render_bracket(prefix="adm_")
            
            if st.button("💾 SALVA RISULTATI ADMIN NEL DATABASE"):
                d = {i: [st.session_state.get(f"adm_h_{i}"), st.session_state.get(f"adm_a_{i}")] for i in range(72)}
                invia_su_foglio("RisultatiReali", "OFFICIAL_ADMIN", d)

    with tabs[3]:
        if st.button("🚀 INVIA PRONOSTICI DEFINITIVAMENTE", type="primary", use_container_width=True):
            user_data = {i: [st.session_state.get(f"h_{i}"), st.session_state.get(f"a_{i}")] for i in range(72)}
            if invia_su_foglio("Pronostici", user, {"g": user_data, "v": st.session_state.get("vincitore")}):
                st.balloons(); st.success("Inviato con successo!")
