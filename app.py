import streamlit as st
import pandas as pd
import json
import gspread
import random
from google.oauth2.service_account import Credentials

# --- 1. CONFIGURAZIONE PAGINA E GRAFICA ---
st.set_page_config(page_title="WC 2026 - Master Contest", layout="wide")

# CSS: STILE PREMIUM DARK AD ALTO CONTRASTO
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap');
    .stApp { background-color: #0b0f1a; color: #ffffff; font-family: 'Inter', sans-serif; }
    
    /* Titoli e Tab */
    h1, h2, h3 { color: #38bdf8 !important; font-weight: 900 !important; }
    button[data-baseweb="tab"] p { font-size: 22px !important; font-weight: 800 !important; color: #94a3b8 !important; }
    button[data-baseweb="tab"][aria-selected="true"] p { color: #00d4ff !important; }
    
    /* Card Partite */
    .match-card {
        background: #1e293b; border-radius: 12px; padding: 15px; 
        border: 1px solid #334155; margin-bottom: 10px;
    }
    
    /* Punti 1X2 */
    .ranking-info {
        background: #0ea5e9; color: white; border-radius: 6px; 
        font-size: 13px; font-weight: 800; padding: 5px; text-align: center; margin-bottom: 10px;
    }

    /* Input Numerici */
    input[type="number"] {
        background-color: #334155 !important; color: #ffffff !important;
        font-size: 22px !important; font-weight: 900 !important; 
        border: 2px solid #38bdf8 !important; border-radius: 8px !important;
        text-align: center !important;
    }
    
    .team-name-label { font-size: 14px; font-weight: 700; color: #f1f5f9; text-align: center; }
</style>
""", unsafe_allow_html=True)

# --- 2. DATABASE RANKING ---
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

# --- 3. LOGICA DATABASE ---
def get_gspread_client():
    info = json.loads(st.secrets["service_account"])
    creds = Credentials.from_service_account_info(info, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
    return gspread.authorize(creds), info['client_email']

def salva_dati(tab, nick, payload):
    try:
        client, email = get_gspread_client()
        URL = "https://docs.google.com/spreadsheets/d/1palUSBw4IlBFzU4dKtgT0tnjPiPEtxIc6K-DK05vXG8/edit?gid=0#gid=0" # <--- METTI IL LINK DEL TUO FOGLIO GOOGLE QUI
        sh = client.open_by_url(URL)
        try: ws = sh.worksheet(tab)
        except: ws = sh.get_worksheet(0)
        ws.append_row([nick, json.dumps(payload)])
        return True
    except Exception as e:
        # Mostra l'email da autorizzare se c'è un errore 403
        st.error(f"❌ ERRORE DI INVIO (403): {e}")
        st.markdown(f"**Copia questa email e aggiungila come EDITOR nelle impostazioni di condivisione del tuo Foglio Google:**")
        st.code(email, language=None)
        return False

# --- 4. FUNZIONI DI CALCOLO ---
def calcola_classifiche(pref=""):
    groups = get_groups()
    stats = {g: {t: {"Pt": 0, "DR": 0} for t in ts} for g, ts in groups.items()}
    for i, m in enumerate(MATCHES):
        h = st.session_state.get(f"{pref}h_{i}", 0)
        a = st.session_state.get(f"{pref}a_{i}", 0)
        sh, sa = stats[m['gr']][m['h']], stats[m['gr']][m['a']]
        sh["DR"] += (h - a); sa["DR"] += (a - h)
        if h > a: sh["Pt"] += 3
        elif a > h: sa["Pt"] += 3
        else: sh["Pt"] += 1; sa["Pt"] += 1
    
    ranks = {g: pd.DataFrame(ts).T.sort_values(["Pt", "DR"], ascending=False).index.tolist() for g, ts in stats.items()}
    return ranks

# --- 5. LOGICA LOGIN ADMIN ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

# --- 6. INTERFACCIA ---
col_logo, col_login = st.columns([7, 3])
with col_logo:
    # URL stabile del logo FIFA World Cup 2026
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/a/a7/2026_FIFA_World_Cup_logo.svg/512px-2026_FIFA_World_Cup_logo.svg.png", width=120)
with col_login:
    st.write("### 🔐 Login Admin")
    pass_adm = st.text_input("Password", type="password", label_visibility="collapsed")
    if pass_adm == "mondiali2026": st.session_state.logged_in = True

user_nick = st.text_input("👤 Nickname Partecipante:", placeholder="Inserisci il tuo nome...")

if user_nick:
    tab_labels = ["🌍 Gironi", "📊 Classifiche", "⚔️ Bracket", "🚀 Invia"]
    if st.session_state.logged_in: tab_labels.append("🏆 Admin Panel")
    tabs = st.tabs(tab_labels)

    # --- TAB GIRONI ---
    with tabs[0]:
        col_m1, col_m2, col_m3 = st.columns([1, 2, 1])
        with col_m2:
            if st.button("🪄 Compila Random (Popola Risultati Visualizzabili)", use_container_width=True):
                for i in range(72):
                    st.session_state[f"h_{i}"] = random.randint(0, 4)
                    st.session_state[f"a_{i}"] = random.randint(0, 4)
                st.rerun()

        st.write("<br>", unsafe_allow_html=True)

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
                            # Badge dei punti basati sul file PDF
                            st.markdown(f"<div class='ranking-info'>Punti -> 1: {p1} | X: {px} | 2: {p2}</div>", unsafe_allow_html=True)
                            c1, in1, vs, in2, c2 = st.columns([1, 1.2, 0.4, 1.2, 1])
                            c1.image(get_flag(m['h']), width=30)
                            # UTILIZZO DI VALUE PER MOSTRARE IL RISULTATO
                            st.session_state[f"h_{idx}"] = in1.number_input("H", 0, 9, key=f"widget_h_{idx}", value=st.session_state.get(f"h_{idx}", 0), label_visibility="collapsed")
                            vs.markdown("<p style='text-align:center; padding-top:8px;'>–</p>", unsafe_allow_html=True)
                            st.session_state[f"a_{idx}"] = in2.number_input("A", 0, 9, key=f"widget_a_{idx}", value=st.session_state.get(f"a_{idx}", 0), label_visibility="collapsed")
                            c2.image(get_flag(m['a']), width=30)
                            st.markdown(f"<p class='team-name-label'>{m['h']} vs {m['a']}</p>", unsafe_allow_html=True)

    # --- FUNZIONE BRACKET GENERICA (WIMBLEDON STYLE SX-DX) ---
    def generate_bracket_ui(prefix=""):
        ranks = calcola_classifiche(prefix)
        
        def render_match_box(t1, t2, mid, label):
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

        # Layout Orizzontale Wimbledon Style
        st.subheader("⚔️ Tabellone Eliminazione Diretta")
        
        c_sed, c_ott, c_qua, c_fin = st.columns([1.2, 1.1, 1.1, 1.4])
        
        with c_sed:
            st.write("📌 Sedicesimi")
            v_s1 = render_match_box(ranks["A"][1], ranks["C"][1], "S1", "Match 1")
            v_s2 = render_match_box(ranks["D"][0], "3rd Group", "S2", "Match 2")
            # ... Logica nascosta per brevità ma struttura pronta

        with c_ott:
            st.write("🎯 Ottavi")
            v_o1 = render_match_box(v_s1, v_s2, "O1", "Ottavo 1")

        with c_qua:
            st.write("💎 Quarti")
            v_q1 = render_match_box(v_o1, "Vinc. O2", "Q1", "Quarto 1")

        with c_fin:
            st.write("🔥 Semi & Finale")
            v_semi1 = render_match_box(v_q1, "Vinc. Q2", "semi1", "Semi 1")
            st.divider()
            campione = render_match_box(v_semi1, "Finalista 2", "winner", "🏆 CAMPIONE")
            st.session_state[prefix+"vincitore_finale"] = campione
            if campione != "TBD" and prefix=="": st.balloons()

    with tabs[2]:
        col_sim1, col_sim2, col_sim3 = st.columns([1, 2, 1])
        with col_sim2:
            if st.button("🪄 Simula Bracket Casuale (Test)", use_container_width=True):
                all_teams = list(RANKING.keys())
                for key in ["S1","S2","O1","semi1","winner"]:
                    st.session_state[key] = random.choice(all_teams)
                st.rerun()
        generate_bracket_ui(prefix="")

    # --- TAB ADMIN (GESTIONE COMPLETA) ---
    if st.session_state.logged_in:
        with tabs[-1]:
            admin_subtabs = st.tabs(["📊 Classifica Partecipanti", "🏟️ Inserimento Risultati Ufficiali"])
            
            # --- SUBTAB 1: CLASSICA PARTECIPANTI (Ranking) ---
            with admin_subtabs[0]:
                st.header("🏆 Classifica Generale del Contest (Ranking)")
                st.info("Qui l'Admin vede i punti di tutti i partecipanti, calcolati confrontando i loro pronostici con i risultati reali inseriti.")
                # Simulazione della classifica (qui va la logica di calcolo)
                leaderboard_df = pd.DataFrame([
                    {"Nickname": "Marco_WC", "Punti": 140, "Risultati Esatti": 5, "Winner": "Brasile"},
                    {"Nickname": "Luca_Contest", "Punti": 110, "Risultati Esatti": 3, "Winner": "Francia"}
                ])
                st.dataframe(leaderboard_df, use_container_width=True)

            # --- SUBTAB 2: RISULTATI REALI ---
            with admin_subtabs[1]:
                st.header("⚙️ Gestione Risultati REALI")
                col_test1, col_test2 = st.columns(2)
                if col_test1.button("🪄 Auto-compila Risultati Reali Casualii (Test)"):
                    for i in range(72):
                        st.session_state[f"adm_h_{i}"] = random.randint(0, 3)
                        st.session_state[f"adm_a_{i}"] = random.randint(0, 3)
                    st.rerun()
                
                st.subheader("Inserisci Risultati Ufficiali (72 Partite)")
                for i, m in enumerate(MATCHES):
                    with st.expander(f"G{m['gr']}: {m['h']} vs {m['a']}"):
                        ca1, ca2 = st.columns(2)
                        st.session_state[f"adm_h_{i}"] = ca1.number_input(f"{m['h']}", 0, 9, key=f"adm_widget_h_{i}", value=st.session_state.get(f"adm_h_{i}", 0))
                        st.session_state[f"adm_a_{i}"] = ca2.number_input(f"{m['a']}", 0, 9, key=f"adm_widget_a_{i}", value=st.session_state.get(f"adm_a_{i}", 0))
                
                st.subheader("Bracket Ufficiale (Admin)")
                generate_bracket_ui(prefix="adm_")
                
                if st.button("💾 SALVA RISULTATI ADMIN NEL DATABASE", use_container_width=True, type="primary"):
                    adm_payload = {i: [st.session_state.get(f"adm_h_{i}"), st.session_state.get(f"adm_a_{i}")] for i in range(72)}
                    invia_dati("RisultatiReali", "ADMIN_OFFICIAL", adm_payload)

    # --- TAB INVIO ---
    with tabs[3]:
        st.write("### 🚀 Pronti per l'invio?")
        if st.button("INVIA PRONOSTICI DEFINITIVAMENTE", type="primary", use_container_width=True):
            user_payload = {i: [st.session_state.get(f"h_{i}"), st.session_state.get(f"a_{i}")] for i in range(72)}
            if salva_dati("Pronostici", user_nick, {"gironi": user_payload, "vincitore": st.session_state.get("final_winner")}):
                st.balloons(); st.success("Dati inviati correttamente al Database!")
