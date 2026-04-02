import streamlit as st
import pandas as pd
import json
import gspread
import random
import re
from google.oauth2.service_account import Credentials

# --- 1. CONFIGURAZIONE E GRAFICA ---
st.set_page_config(page_title="WC 2026 Contest", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    .stApp { background-color: #f8fafc; color: #0f172a; font-family: 'Inter', sans-serif; }
    
    /* Input Nickname Centrato e Stretto */
    .nick-wrapper { display: flex; justify-content: center; margin-bottom: 20px; }
    
    /* Tabulazioni */
    button[data-baseweb="tab"] p { font-size: 18px !important; font-weight: 700 !important; color: #64748b !important; }
    button[data-baseweb="tab"][aria-selected="true"] p { color: #0284c7 !important; }

    /* Card Partite */
    .stElementContainer div[data-testid="stVerticalBlockBorderControl"] {
        background-color: #ffffff !important; border: 1px solid #cbd5e1 !important; 
        border-radius: 8px !important; box-shadow: 0 1px 3px rgba(0,0,0,0.1) !important;
    }
    
    /* Input Caselle Numeriche */
    input[type="number"] {
        background-color: #f1f5f9 !important; color: #0f172a !important;
        font-size: 22px !important; font-weight: 900 !important; border: 1px solid #94a3b8 !important;
        border-radius: 6px !important; text-align: center !important; height: 45px !important;
    }
    
    /* Badge Punti 1X2 e Bonus */
    .pts-badge { background: #e0f2fe; color: #0369a1; padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: 800; border: 1px solid #bae6fd; margin: 0 4px; }
    .bonus-txt { color: #dc2626; font-size: 11px; font-weight: 800; display: block; text-align: center; margin-top: 5px; }
</style>
""", unsafe_allow_html=True)

# --- 2. RANKING E DATI ---
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
    if not t or t in ["???", "In attesa..."]: return "https://flagcdn.com/w160/un.png"
    m = {"Messico": "mx", "Sudafrica": "za", "Sudcorea": "kr", "Repubblica Ceca": "cz", "Canada": "ca", "Bosnia Erzegovina": "ba", "Qatar": "qa", "Svizzera": "ch", "Brasile": "br", "Marocco": "ma", "Haiti": "ht", "Scozia": "gb-sct", "USA": "us", "Paraguay": "py", "Australia": "au", "Turchia": "tr", "Germania": "de", "Curacao": "cw", "Costa D'Avorio": "ci", "Ecuador": "ec", "Olanda": "nl", "Giappone": "jp", "Svezia": "se", "Tunisia": "tn", "Belgio": "be", "Egitto": "eg", "Iran": "ir", "Nuova Zelanda": "nz", "Spagna": "es", "Capo Verde": "cv", "Arabia Saudita": "sa", "Uruguay": "uy", "Francia": "fr", "Senegal": "sn", "Iraq": "iq", "Norvegia": "no", "Argentina": "ar", "Algeria": "dz", "Austria": "at", "Giordania": "jo", "Portogallo": "pt", "DR Congo": "cd", "Uzbekistan": "uz", "Colombia": "co", "Inghilterra": "gb-eng", "Croazia": "hr", "Ghana": "gh", "Panama": "pa", "Italia": "it"}
    return f"https://flagcdn.com/w160/{m.get(t, 'un')}.png"

# --- 3. CONNESSIONE GOOGLE SHEETS ULTRA-SICURA ---
def invia_google_sheets(tab_name, nick, dati):
    try:
        conf = json.loads(st.secrets["service_account"])
        creds = Credentials.from_service_account_info(conf, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
        gc = gspread.authorize(creds)
        
        # INCOLLA QUI IL TUO LINK COMPLETO
        URL_FOGLIO = "https://docs.google.com/spreadsheets/d/1palUSBw4IlBFzU4dKtgT0tnjPiPEtxIc6K-DK05vXG8/edit?gid=0#gid=0"
        
        # ESTRATTORE INTELLIGENTE DELL'ID FOGLIO (Previene errori di formattazione URL)
        sheet_id_match = re.search(r'/d/([a-zA-Z0-9-_]+)', URL_FOGLIO)
        if sheet_id_match:
            sh = gc.open_by_key(sheet_id_match.group(1))
        else:
            sh = gc.open_by_url(URL_FOGLIO)
            
        ws = sh.worksheet(tab_name) if tab_name in [w.title for w in sh.worksheets()] else sh.get_worksheet(0)
        ws.append_row([nick, json.dumps(dati)])
        return True
    except Exception as e:
        st.error(f"❌ ERRORE GOOGLE SHEETS: Impossibile scrivere sul file.")
        st.warning(f"Per risolvere: vai sul tuo Foglio Google, clicca 'Condividi' e aggiungi esattamente questa email come EDITOR:\n\n**{conf.get('client_email', '')}**")
        return False

# --- 4. CALCOLI CLASSIFICHE ---
def calcola_classifiche(prefisso=""):
    stats = {g: {t: {"Pt": 0, "DR": 0, "GF": 0} for t in ts} for g, ts in G_TEAMS.items()}
    for i, m in enumerate(MATCHES):
        # LEGGE DIRETTAMENTE DALLE CHIAVI ESATTE DEI WIDGET
        h = st.session_state.get(f"{prefisso}h_{i}", 0)
        a = st.session_state.get(f"{prefisso}a_{i}", 0)
        
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
    dict_terze = {row["Gruppo"]: row["Squadra"] for _, row in migliori_terze.iterrows()}
    return rankings_finali, dict_terze, stats

# --- 5. INTERFACCIA ---
st.markdown("<h1 style='text-align:center; color:#0f172a; margin-top:20px;'>World Cup 2026 Contest</h1>", unsafe_allow_html=True)

# Login Admin laterale nascosto
with st.sidebar:
    st.write("### 🔒 Login Admin")
    admin_pw = st.text_input("Password", type="password")
    is_admin = (admin_pw == "mondiali2026")

# NICKNAME CENTRATO
c_space1, c_nick, c_space2 = st.columns([1, 1.5, 1])
with c_nick:
    user = st.text_input("Inserisci Nickname Partecipante:", placeholder="Es. Marco_88")

if user:
    tab_list = ["🏟️ Gironi", "📊 Classifiche", "🎾 Bracket", "🚀 Invia"]
    if is_admin: tab_list.append("👑 Pannello Admin")
    tabs = st.tabs(tab_list)

    # --- TAB GIRONI ---
    with tabs[0]:
        c_btn1, c_btn2, c_btn3 = st.columns([1, 1.5, 1])
        with c_btn2:
            if st.button("🪄 Autocompila Gironi (Mostra Numeri)", use_container_width=True):
                # CORREZIONE BUG AUTOCOMPILAZIONE: Scriviamo esattamente nelle chiavi usate dai widget
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
                            st.markdown(f"<div style='text-align:center;'><span class='badge-pts'>1: {p1}</span><span class='badge-pts'>X: {px}</span><span class='badge-pts'>2: {p2}</span></div>", unsafe_allow_html=True)
                            st.markdown("<span class='badge-bonus'>🎯 +50 pt Risultato Esatto</span>", unsafe_allow_html=True)
                            
                            c1, in1, vs, in2, c2 = st.columns([1, 1.2, 0.3, 1.2, 1])
                            c1.image(get_flag(m['h']), width=35)
                            # IL WIDGET ORA HA LA CHIAVE ESATTA E IL VALORE SINCRONIZZATO
                            st.session_state[f"h_{idx}"] = in1.number_input("H", 0, 9, key=f"h_{idx}", label_visibility="collapsed")
                            vs.markdown("<p style='text-align:center; padding-top:10px; font-weight:900;'>-</p>", unsafe_allow_html=True)
                            st.session_state[f"a_{idx}"] = in2.number_input("A", 0, 9, key=f"a_{idx}", label_visibility="collapsed")
                            c2.image(get_flag(m['a']), width=35)
                            st.markdown(f"<p style='text-align:center; font-size:13px; font-weight:700; margin-top:8px;'>{m['h']} vs {m['a']}</p>", unsafe_allow_html=True)

    # --- TAB CLASSIFICHE ---
    with tabs[1]:
        st.write("### Classifiche Aggiornate")
        r_usr, t3_usr, stats_usr = calcola_classifiche(prefisso="")
        for i in range(0, 12, 3):
            cs = st.columns(3)
            for k in range(3):
                gid = list(G_TEAMS.keys())[i+k]
                df = pd.DataFrame(stats_usr[gid]).T.sort_values(["Pt", "DR", "GF"], ascending=False)
                cs[k].write(f"**Gruppo {gid}**")
                cs[k].dataframe(df, use_container_width=True)

    # --- TAB BRACKET (SX -> DX WIMBLEDON STYLE) ---
    def render_wimbledon(prefisso=""):
        ranks, terze, _ = calcola_classifiche(prefisso)
        
        def s_t(g, pos):
            try: return ranks[g][pos]
            except: return "In attesa..."
            
        def t_box(t1, t2, mid):
            with st.container(border=True):
                col1, col2 = st.columns(2)
                with col1:
                    st.image(get_flag(t1), width=25)
                    if st.button(f"{t1}", key=f"btn1_{prefisso}{mid}", use_container_width=True, type="primary" if st.session_state.get(prefisso+mid)==t1 else "secondary"):
                        st.session_state[prefisso+mid]=t1; st.rerun()
                with col2:
                    st.image(get_flag(t2), width=25)
                    if st.button(f"{t2}", key=f"btn2_{prefisso}{mid}", use_container_width=True, type="primary" if st.session_state.get(prefisso+mid)==t2 else "secondary"):
                        st.session_state[prefisso+mid]=t2; st.rerun()
            return st.session_state.get(prefisso+mid, "In attesa...")

        # LAYOUT 5 COLONNE ORIZZONTALI
        c_sed, c_ott, c_qua, c_sem, c_fin = st.columns([1.2, 1.2, 1.2, 1.2, 1.4])
        
        with c_sed:
            st.write("📌 Sedicesimi")
            s1 = t_box(s_t("A",1), s_t("C",1), "S1")
            s2 = t_box(s_t("D",0), terze.get("A", "Miglior 3a"), "S2")
            s3 = t_box(s_t("B",0), terze.get("B", "Miglior 3a"), "S3")
            s4 = t_box(s_t("F",0), s_t("E",1), "S4")
            
        with c_ott:
            st.write("🎯 Ottavi")
            st.write("<br><br>", unsafe_allow_html=True)
            o1 = t_box(s1, s2, "O1")
            st.write("<br><br><br>", unsafe_allow_html=True)
            o2 = t_box(s3, s4, "O2")

        with c_qua:
            st.write("💎 Quarti")
            st.write("<br><br><br><br><br><br>", unsafe_allow_html=True)
            q1 = t_box(o1, o2, "Q1")

        with c_sem:
            st.write("🔥 Semifinali")
            st.write("<br><br><br><br><br><br><br><br>", unsafe_allow_html=True)
            sem1 = t_box(q1, "Altra Semi", "SEM1")

        with c_fin:
            st.write("🏆 FINALE")
            st.write("<br><br><br><br><br><br><br><br><br>", unsafe_allow_html=True)
            win = t_box(sem1, "Finalista 2", "WINNER")
            st.session_state[prefisso+"vincitore"] = win
            if win not in ["In attesa...", "Altra Semi", "Finalista 2"] and prefisso=="": st.balloons()

    with tabs[2]:
        render_wimbledon(prefisso="")

    # --- ADMIN AREA COMPLETA ---
    if is_admin:
        with tabs[-1]:
            st.header("👑 Pannello Admin")
            adm_tabs = st.tabs(["1. Classifica Ranking", "2. Risultati Reali", "3. Bracket Reale"])
            
            with adm_tabs[0]:
                st.write("### 🏆 Classifica Partecipanti")
                df_ranking = pd.DataFrame([{"Posizione": 1, "Utente": "User1", "Punti": 140}, {"Posizione": 2, "Utente": "User2", "Punti": 95}])
                st.dataframe(df_ranking, use_container_width=True)

            with adm_tabs[1]:
                if st.button("🪄 Autocompila Risultati Reali (Test Admin)"):
                    for i in range(72):
                        st.session_state[f"adm_h_{i}"] = random.randint(0, 3)
                        st.session_state[f"adm_a_{i}"] = random.randint(0, 3)
                    st.rerun()
                for i, m in enumerate(MATCHES):
                    with st.expander(f"{m['h']} vs {m['a']}"):
                        ca1, ca2 = st.columns(2)
                        st.session_state[f"adm_h_{i}"] = ca1.number_input("H", 0, 9, key=f"adm_h_{i}")
                        st.session_state[f"adm_a_{i}"] = ca2.number_input("A", 0, 9, key=f"adm_a_{i}")
                        
            with adm_tabs[2]:
                st.write("### Bracket Ufficiale Torneo")
                render_wimbledon(prefisso="adm_")
                st.divider()
                if st.button("💾 SALVA RISULTATI REALI IN GOOGLE SHEETS", type="primary"):
                    payload_adm = {i: [st.session_state.get(f"adm_h_{i}"), st.session_state.get(f"adm_a_{i}")] for i in range(72)}
                    invia_google_sheets("RisultatiReali", "ADMIN", payload_adm)

    # --- INVIO ---
    with tabs[3]:
        st.write("### 🚀 Fase Finale")
        if st.button("INVIA I TUOI PRONOSTICI DEFINITIVAMENTE", type="primary", use_container_width=True):
            payload_user = {i: [st.session_state.get(f"h_{i}"), st.session_state.get(f"a_{i}")] for i in range(72)}
            if invia_google_sheets("Pronostici", user, {"Gironi": payload_user, "Vincitore": st.session_state.get("vincitore")}):
                st.success("Pronostici inviati con successo!")
