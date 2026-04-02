import streamlit as st
import pandas as pd
import json
import gspread
import random
import re
from google.oauth2.service_account import Credentials

# --- 1. CONFIGURAZIONE E GRAFICA ---
st.set_page_config(page_title="FIFA World Cup 2026 Contest", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    .stApp { background-color: #f8fafc; color: #0f172a; font-family: 'Inter', sans-serif; }
    
    .nick-wrapper { display: flex; justify-content: center; margin-bottom: 20px; }
    button[data-baseweb="tab"] p { font-size: 18px !important; font-weight: 700 !important; color: #64748b !important; }
    button[data-baseweb="tab"][aria-selected="true"] p { color: #0284c7 !important; }

    .stElementContainer div[data-testid="stVerticalBlockBorderControl"] {
        background-color: #ffffff !important; border: 1px solid #cbd5e1 !important; 
        border-radius: 8px !important; box-shadow: 0 1px 3px rgba(0,0,0,0.1) !important;
    }
    
    input[type="number"] {
        background-color: #f1f5f9 !important; color: #0f172a !important;
        font-size: 22px !important; font-weight: 900 !important; border: 1px solid #94a3b8 !important;
        border-radius: 6px !important; text-align: center !important; height: 45px !important;
    }
    
    .pts-badge { background: #e0f2fe; color: #0369a1; padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: 800; border: 1px solid #bae6fd; margin: 0 4px; }
    .bonus-txt { color: #dc2626; font-size: 11px; font-weight: 800; display: block; text-align: center; margin-top: 5px; }
</style>
""", unsafe_allow_html=True)

# --- 2. INIZIALIZZAZIONE MEMORIA (ANTI-CRASH) ---
if "initialized" not in st.session_state:
    for i in range(72):
        st.session_state[f"h_{i}"] = 0
        st.session_state[f"a_{i}"] = 0
        st.session_state[f"adm_h_{i}"] = 0
        st.session_state[f"adm_a_{i}"] = 0
    # Inizializzo le partite del bracket
    for k in [f"S{i}" for i in range(1,17)] + [f"O{i}" for i in range(1,9)] + [f"Q{i}" for i in range(1,5)] + ["SEM1", "SEM2", "WINNER"]:
        st.session_state[k] = "TBD"
        st.session_state[f"adm_{k}"] = "TBD"
    st.session_state["initialized"] = True

# --- 3. RANKING E DATI ---
RANKING = {
    "Spagna": 1, "Argentina": 2, "Francia": 3, "Inghilterra": 4, "Brasile": 5, "Portogallo": 6, "Olanda": 7, "Belgio": 8,
    "Germania": 9, "Croazia": 10, "Marocco": 11, "Colombia": 13, "Italia": 13, "USA": 14, "Messico": 15, "Uruguay": 16,
    "Svizzera": 17, "Giappone": 18, "Senegal": 19, "Iran": 20, "Sudcorea": 22, "Ecuador": 23, "Austria": 24, "Turchia": 25,
    "Australia": 26, "Canada": 27, "Norvegia": 29, "Panama": 30, "Egitto": 34, "Algeria": 35, "Scozia": 36, "Paraguay": 39,
    "Tunisia": 40, "Costa D'Avorio": 42, "Svezia": 43, "Repubblica Ceca": 44, "Uzbekistan": 50, "DR Congo": 56, "Qatar": 58,
    "Iraq": 58, "Arabia Saudita": 60, "Sudafrica": 61, "Giordania": 66, "Capo Verde": 68, "Bosnia Erzegovina": 71, "Ghana": 72,
    "Curacao": 82, "Haiti": 84, "Nuova Zelanda": 86
}

G_TEAMS = {
    "A": ["Messico", "Sudafrica", "Sudcorea", "Repubblica Ceca"], "B": ["Canada", "Bosnia Erzegovina", "Qatar", "Svizzera"],
    "C": ["Brasile", "Marocco", "Haiti", "Scozia"], "D": ["USA", "Paraguay", "Australia", "Turchia"],
    "E": ["Germania", "Curacao", "Costa D'Avorio", "Ecuador"], "F": ["Olanda", "Giappone", "Svezia", "Tunisia"],
    "G": ["Belgio", "Egitto", "Iran", "Nuova Zelanda"], "H": ["Spagna", "Capo Verde", "Arabia Saudita", "Uruguay"],
    "I": ["Francia", "Senegal", "Iraq", "Norvegia"], "J": ["Argentina", "Algeria", "Austria", "Giordania"],
    "K": ["Portogallo", "DR Congo", "Uzbekistan", "Colombia"], "L": ["Inghilterra", "Croazia", "Ghana", "Panama"]
}

MATCHES = []
for gid, teams in G_TEAMS.items():
    for h, a in [(0, 1), (2, 3), (0, 2), (1, 3), (0, 3), (1, 2)]:
        MATCHES.append({"gr": gid, "h": teams[h], "a": teams[a]})

def get_flag(t):
    if not t or t in ["TBD", "In attesa..."]: return "https://flagcdn.com/w160/un.png"
    m = {"Messico": "mx", "Sudafrica": "za", "Sudcorea": "kr", "Repubblica Ceca": "cz", "Canada": "ca", "Bosnia Erzegovina": "ba", "Qatar": "qa", "Svizzera": "ch", "Brasile": "br", "Marocco": "ma", "Haiti": "ht", "Scozia": "gb-sct", "USA": "us", "Paraguay": "py", "Australia": "au", "Turchia": "tr", "Germania": "de", "Curacao": "cw", "Costa D'Avorio": "ci", "Ecuador": "ec", "Olanda": "nl", "Giappone": "jp", "Svezia": "se", "Tunisia": "tn", "Belgio": "be", "Egitto": "eg", "Iran": "ir", "Nuova Zelanda": "nz", "Spagna": "es", "Capo Verde": "cv", "Arabia Saudita": "sa", "Uruguay": "uy", "Francia": "fr", "Senegal": "sn", "Iraq": "iq", "Norvegia": "no", "Argentina": "ar", "Algeria": "dz", "Austria": "at", "Giordania": "jo", "Portogallo": "pt", "DR Congo": "cd", "Uzbekistan": "uz", "Colombia": "co", "Inghilterra": "gb-eng", "Croazia": "hr", "Ghana": "gh", "Panama": "pa", "Italia": "it"}
    return f"https://flagcdn.com/w160/{m.get(t, 'un')}.png"

# --- 4. CONNESSIONE GOOGLE SHEETS ---
def invia_google_sheets(tab_name, nick, dati):
    try:
        conf = json.loads(st.secrets["service_account"])
        creds = Credentials.from_service_account_info(conf, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
        gc = gspread.authorize(creds)
        
        # INSERISCI QUI L'ID DEL FOGLIO!
        ID_DEL_FOGLIO = "1palUSBw4IlBFzU4dKtgT0tnjPiPEtxIc6K-DK05vXG8" 
        
        sh = gc.open_by_key(ID_DEL_FOGLIO)
        ws = sh.worksheet(tab_name) if tab_name in [w.title for w in sh.worksheets()] else sh.get_worksheet(0)
        ws.append_row([nick, json.dumps(dati)])
        return True
    except Exception as e:
        st.error(f"❌ ERRORE: Impossibile scrivere sul file.")
        return False

# --- 5. CALCOLI CLASSIFICHE ---
def calcola_classifiche(prefisso=""):
    stats = {g: {t: {"Pt": 0, "DR": 0, "GF": 0} for t in ts} for g, ts in G_TEAMS.items()}
    for i, m in enumerate(MATCHES):
        h = st.session_state[f"{prefisso}h_{i}"]
        a = st.session_state[f"{prefisso}a_{i}"]
        
        stats[m['gr']][m['h']]["GF"] += h; stats[m['gr']][m['a']]["GF"] += a
        stats[m['gr']][m['h']]["DR"] += (h - a); stats[m['gr']][m['a']]["DR"] += (a - h)
        if h > a: stats[m['gr']][m['h']]["Pt"] += 3
        elif a > h: stats[m['gr']][m['a']]["Pt"] += 3
        else: stats[m['gr']][m['h']]["Pt"] += 1; stats[m['gr']][m['a']]["Pt"] += 1

    rankings_finali = {}
    terze_squadre = []
    for g, ts in stats.items():
        df = pd.DataFrame(ts).T.sort_values(["Pt", "DR", "GF"], ascending=False)
        rankings_finali[g] = df.index.tolist()
        terze_squadre.append({"Squadra": df.index[2], "Pt": df.iloc[2]["Pt"], "DR": df.iloc[2]["DR"], "Gruppo": g})
    
    migliori_terze = pd.DataFrame(terze_squadre).sort_values(["Pt", "DR"], ascending=False).head(8)
    list_terze = migliori_terze["Squadra"].tolist()
    return rankings_finali, list_terze, stats

# --- 6. INTERFACCIA ---
st.markdown("<h1 style='text-align:center; color:#0f172a; margin-top:10px;'>🏆 World Cup 2026 Contest</h1>", unsafe_allow_html=True)

with st.sidebar:
    st.write("### 🔒 Login Admin")
    admin_pw = st.text_input("Password", type="password")
    is_admin = (admin_pw == "mondiali2026")

c_space1, c_nick, c_space2 = st.columns([1, 1.5, 1])
with c_nick:
    user = st.text_input("Inserisci Nickname Partecipante:", placeholder="Es. Marco_88")

if user:
    tab_list = ["🏟️ Gironi", "📊 Classifiche", "🎾 Bracket Completo", "🚀 Invia"]
    if is_admin: tab_list.append("👑 Pannello Admin")
    tabs = st.tabs(tab_list)

    # --- TAB GIRONI ---
    with tabs[0]:
        c_btn1, c_btn2, c_btn3 = st.columns([1, 1.5, 1])
        with c_btn2:
            if st.button("🪄 Autocompila Gironi", use_container_width=True):
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
                            st.markdown(f"<div style='text-align:center;'><span class='pts-badge'>1: {p1}pt</span><span class='pts-badge'>X: {px}pt</span><span class='pts-badge'>2: {p2}pt</span></div>", unsafe_allow_html=True)
                            st.markdown("<span class='bonus-txt'>🎯 +50 pt Risultato Esatto</span>", unsafe_allow_html=True)
                            
                            c1, in1, vs, in2, c2 = st.columns([1, 1.2, 0.3, 1.2, 1])
                            c1.image(get_flag(m['h']), width=30)
                            in1.number_input("H", min_value=0, max_value=9, key=f"h_{idx}", label_visibility="collapsed")
                            vs.markdown("<p style='text-align:center; padding-top:6px; font-weight:900;'>-</p>", unsafe_allow_html=True)
                            in2.number_input("A", min_value=0, max_value=9, key=f"a_{idx}", label_visibility="collapsed")
                            c2.image(get_flag(m['a']), width=30)
                            st.markdown(f"<p style='text-align:center; font-size:12px; font-weight:700; margin-top:5px;'>{m['h']} v {m['a']}</p>", unsafe_allow_html=True)

    # --- TAB CLASSIFICHE ---
    with tabs[1]:
        r_usr, t3_usr, stats_usr = calcola_classifiche(prefisso="")
        for i in range(0, 12, 3):
            cs = st.columns(3)
            for k in range(3):
                gid = list(G_TEAMS.keys())[i+k]
                df = pd.DataFrame(stats_usr[gid]).T.sort_values(["Pt", "DR", "GF"], ascending=False)
                cs[k].write(f"**Gruppo {gid}**")
                cs[k].dataframe(df, use_container_width=True)

    # --- TAB BRACKET (TORNEO INTERO) ---
    def render_wimbledon(prefisso=""):
        ranks, terze_list, _ = calcola_classifiche(prefisso)
        
        def s_t(g, pos):
            try: return ranks[g][pos]
            except: return "TBD"
            
        def s_t3(index):
            try: return terze_list[index]
            except: return "TBD"
            
        def t_box(t1, t2, mid):
            with st.container(border=True):
                st.markdown(f"<div style='font-size:10px; color:#94a3b8; font-weight:700;'>{mid}</div>", unsafe_allow_html=True)
                if st.button(t1, key=f"btn1_{prefisso}{mid}", use_container_width=True, type="primary" if st.session_state[prefisso+mid]==t1 else "secondary"):
                    st.session_state[prefisso+mid]=t1; st.rerun()
                if st.button(t2, key=f"btn2_{prefisso}{mid}", use_container_width=True, type="primary" if st.session_state[prefisso+mid]==t2 else "secondary"):
                    st.session_state[prefisso+mid]=t2; st.rerun()
            return st.session_state[prefisso+mid]

        st.info("I nomi appaiono in base alle classifiche dei gironi. Clicca sui vincitori per farli avanzare nel tabellone.")
        c_sed, c_ott, c_qua, c_sem, c_fin = st.columns(5)
        
        with c_sed:
            st.markdown("<p style='font-weight:800; color:#475569;'>Sedicesimi (32)</p>", unsafe_allow_html=True)
            s1 = t_box(s_t("A",0), s_t3(0), "S1")
            s2 = t_box(s_t("B",1), s_t("C",1), "S2")
            s3 = t_box(s_t("D",0), s_t3(1), "S3")
            s4 = t_box(s_t("E",1), s_t("F",1), "S4")
            s5 = t_box(s_t("G",0), s_t3(2), "S5")
            s6 = t_box(s_t("H",1), s_t("I",1), "S6")
            s7 = t_box(s_t("J",0), s_t3(3), "S7")
            s8 = t_box(s_t("K",1), s_t("L",1), "S8")
            s9 = t_box(s_t("B",0), s_t3(4), "S9")
            s10= t_box(s_t("E",0), s_t("A",1), "S10")
            s11= t_box(s_t("C",0), s_t3(5), "S11")
            s12= t_box(s_t("F",0), s_t("D",1), "S12")
            s13= t_box(s_t("H",0), s_t3(6), "S13")
            s14= t_box(s_t("K",0), s_t("G",1), "S14")
            s15= t_box(s_t("I",0), s_t3(7), "S15")
            s16= t_box(s_t("L",0), s_t("J",1), "S16")
            
        with c_ott:
            st.markdown("<p style='font-weight:800; color:#475569;'>Ottavi (16)</p>", unsafe_allow_html=True)
            st.markdown("<div style='height:40px;'></div>", unsafe_allow_html=True)
            o1 = t_box(s1, s2, "O1")
            st.markdown("<div style='height:80px;'></div>", unsafe_allow_html=True)
            o2 = t_box(s3, s4, "O2")
            st.markdown("<div style='height:80px;'></div>", unsafe_allow_html=True)
            o3 = t_box(s5, s6, "O3")
            st.markdown("<div style='height:80px;'></div>", unsafe_allow_html=True)
            o4 = t_box(s7, s8, "O4")
            st.markdown("<div style='height:80px;'></div>", unsafe_allow_html=True)
            o5 = t_box(s9, s10, "O5")
            st.markdown("<div style='height:80px;'></div>", unsafe_allow_html=True)
            o6 = t_box(s11, s12, "O6")
            st.markdown("<div style='height:80px;'></div>", unsafe_allow_html=True)
            o7 = t_box(s13, s14, "O7")
            st.markdown("<div style='height:80px;'></div>", unsafe_allow_html=True)
            o8 = t_box(s15, s16, "O8")

        with c_qua:
            st.markdown("<p style='font-weight:800; color:#475569;'>Quarti (8)</p>", unsafe_allow_html=True)
            st.markdown("<div style='height:120px;'></div>", unsafe_allow_html=True)
            q1 = t_box(o1, o2, "Q1")
            st.markdown("<div style='height:260px;'></div>", unsafe_allow_html=True)
            q2 = t_box(o3, o4, "Q2")
            st.markdown("<div style='height:260px;'></div>", unsafe_allow_html=True)
            q3 = t_box(o5, o6, "Q3")
            st.markdown("<div style='height:260px;'></div>", unsafe_allow_html=True)
            q4 = t_box(o7, o8, "Q4")

        with c_sem:
            st.markdown("<p style='font-weight:800; color:#475569;'>Semi (4)</p>", unsafe_allow_html=True)
            st.markdown("<div style='height:300px;'></div>", unsafe_allow_html=True)
            sem1 = t_box(q1, q2, "SEM1")
            st.markdown("<div style='height:580px;'></div>", unsafe_allow_html=True)
            sem2 = t_box(q3, q4, "SEM2")

        with c_fin:
            st.markdown("<p style='font-weight:800; color:#1d4ed8;'>FINALE</p>", unsafe_allow_html=True)
            st.markdown("<div style='height:600px;'></div>", unsafe_allow_html=True)
            vinc_key = "adm_vincitore" if prefisso == "adm_" else "WINNER"
            win = t_box(sem1, sem2, "WINNER")
            st.session_state[vinc_key] = win

    with tabs[2]:
        render_wimbledon(prefisso="")

    # --- ADMIN AREA ---
    if is_admin:
        with tabs[-1]:
            st.header("👑 Pannello Admin")
            adm_tabs = st.tabs(["1. Nomi Partecipanti", "2. Risultati Reali", "3. Bracket Reale"])
            
            with adm_tabs[0]:
                st.write("### 🏆 Nomi di chi ha inviato i pronostici")
                try:
                    conf = json.loads(st.secrets["service_account"])
                    creds = Credentials.from_service_account_info(conf, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
                    gc = gspread.authorize(creds)
                    ID_DEL_FOGLIO = "INSERISCI_QUI_SOLO_L_ID_DEL_FOGLIO" # Metti lo stesso ID anche qui!
                    sh = gc.open_by_key(ID_DEL_FOGLIO)
                    ws = sh.worksheet("Pronostici")
                    dati = ws.get_all_values()
                    utenti = list(dict.fromkeys([row[0] for row in dati if len(row) > 0]))
                    if utenti:
                        st.dataframe(pd.DataFrame({"Partecipante": utenti, "Stato": "Salvato"}), use_container_width=True)
                    else:
                        st.info("Nessun partecipante ha ancora giocato.")
                except Exception as e:
                    st.warning("Assicurati di aver configurato il file Google Sheets per vedere la lista.")

            with adm_tabs[1]:
                if st.button("🪄 Autocompila Risultati Reali (Test Admin)"):
                    for i in range(72):
                        st.session_state[f"adm_h_{i}"] = random.randint(0, 3)
                        st.session_state[f"adm_a_{i}"] = random.randint(0, 3)
                    st.rerun()
                for i, m in enumerate(MATCHES):
                    with st.expander(f"{m['h']} vs {m['a']}"):
                        ca1, ca2 = st.columns(2)
                        ca1.number_input("H", 0, 9, key=f"adm_h_{i}")
                        ca2.number_input("A", 0, 9, key=f"adm_a_{i}")
                        
            with adm_tabs[2]:
                render_wimbledon(prefisso="adm_")
                st.divider()
                if st.button("💾 SALVA RISULTATI E TABELLONE REALE IN GOOGLE SHEETS", type="primary"):
                    payload_adm = {i: [st.session_state[f"adm_h_{i}"], st.session_state[f"adm_a_{i}"]] for i in range(72)}
                    
                    # Salva anche il tabellone admin per Google Sheets
                    chiavi_bracket_adm = [f"adm_{k}" for k in [f"S{i}" for i in range(1,17)] + [f"O{i}" for i in range(1,9)] + [f"Q{i}" for i in range(1,5)] + ["SEM1", "SEM2", "WINNER"]]
                    payload_adm_bracket = {k: st.session_state[k] for k in chiavi_bracket_adm}
                    
                    invia_google_sheets("RisultatiReali", "ADMIN", {"Gironi": payload_adm, "Bracket": payload_adm_bracket})

    # --- INVIO ---
    with tabs[3]:
        st.write("### 🚀 Fase Finale")
        if st.button("INVIA I TUOI PRONOSTICI DEFINITIVAMENTE", type="primary", use_container_width=True):
            payload_user = {i: [st.session_state[f"h_{i}"], st.session_state[f"a_{i}"]] for i in range(72)}
            
            # Recupera anche il Bracket compilato dall'utente
            chiavi_bracket = [f"S{i}" for i in range(1,17)] + [f"O{i}" for i in range(1,9)] + [f"Q{i}" for i in range(1,5)] + ["SEM1", "SEM2", "WINNER"]
            payload_bracket = {k: st.session_state[k] for k in chiavi_bracket}
            
            if invia_google_sheets("Pronostici", user, {"Gironi": payload_user, "Bracket": payload_bracket}):
                st.success("Pronostici e Tabellone inviati con successo!")
