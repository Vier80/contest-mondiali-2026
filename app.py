import streamlit as st
import pandas as pd
import json
import gspread
import random
from google.oauth2.service_account import Credentials

# ==========================================
# 1. CONFIGURAZIONE E GRAFICA WIMBLEDON
# ==========================================
st.set_page_config(page_title="WC 2026 Contest", layout="wide")

st.markdown("""
<style>
    /* STILE CHIARO, PULITO E PROFESSIONALE */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    .stApp { background-color: #f8fafc; color: #0f172a; font-family: 'Inter', sans-serif; }
    
    /* Titoli Tab */
    button[data-baseweb="tab"] { height: 50px !important; }
    button[data-baseweb="tab"] p { font-size: 18px !important; font-weight: 700 !important; color: #475569 !important; }
    button[data-baseweb="tab"][aria-selected="true"] p { color: #2563eb !important; }

    /* Card delle partite */
    .stElementContainer div[data-testid="stVerticalBlockBorderControl"] {
        background-color: #ffffff !important; border: 1px solid #cbd5e1 !important; 
        border-radius: 8px !important; box-shadow: 0 1px 3px rgba(0,0,0,0.1) !important;
    }
    
    /* Input per i gol */
    input[type="number"] {
        background-color: #f1f5f9 !important; color: #0f172a !important;
        font-size: 24px !important; font-weight: 900 !important; border: 1px solid #94a3b8 !important;
        border-radius: 6px !important; text-align: center !important; height: 45px !important;
    }
    
    /* Badge Punteggi e Bonus */
    .badge-pts { background: #e0f2fe; color: #0369a1; padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: 800; border: 1px solid #bae6fd; margin: 0 5px; }
    .badge-bonus { color: #dc2626; font-size: 11px; font-weight: 800; display: block; text-align: center; margin-top: 6px; }
    
    /* Layout Bracket Wimbledon */
    .bracket-col { border-right: 1px dashed #cbd5e1; padding-right: 10px; }
    .bracket-match { border-bottom: 2px solid #e2e8f0; margin-bottom: 15px; padding-bottom: 5px; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. DATI E RANKING (ESATTI DA PDF)
# ==========================================
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

# ==========================================
# 3. MOTORE LOGICO E GOOGLE SHEETS
# ==========================================
def invia_google_sheets(tab_name, nick, dati):
    try:
        conf = json.loads(st.secrets["service_account"])
        creds = Credentials.from_service_account_info(conf, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
        client = gspread.authorize(creds)
        
        # INSERISCI QUI IL TUO LINK GOOGLE SHEETS
        URL_FOGLIO = "https://docs.google.com/spreadsheets/d/1palUSBw4IlBFzU4dKtgT0tnjPiPEtxIc6K-DK05vXG8/edit?gid=0#gid=0"
        
        sh = client.open_by_url(URL_FOGLIO)
        ws = sh.worksheet(tab_name) if tab_name in [w.title for w in sh.worksheets()] else sh.get_worksheet(0)
        ws.append_row([nick, json.dumps(dati)])
        return True
    except Exception as e:
        # MESSAGGIO ERRORE CHIARO PER IL 403
        st.error("❌ ACCESSO NEGATO A GOOGLE SHEETS (Errore 403) ❌")
        st.warning(f"Devi aprire il tuo file Excel online, cliccare su 'Condividi' in alto a destra e incollare questa esatta email dandole i permessi di EDITOR:\n\n**{conf.get('client_email', 'Email non trovata nei secrets')}**")
        return False

def calcola_classifiche(prefisso=""):
    stats = {g: {t: {"Pt": 0, "DR": 0, "GF": 0} for t in ts} for g, ts in G_TEAMS.items()}
    for i, m in enumerate(MATCHES):
        h = st.session_state.get(f"{prefisso}h_{i}", 0)
        a = st.session_state.get(f"{prefisso}a_{i}", 0)
        
        # Solo se la partita è stata "giocata" (cioè se i valori sono stati toccati, assumiamo sempre giocata per semplicità di bracket)
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

# ==========================================
# 4. INTERFACCIA PRINCIPALE
# ==========================================
st.markdown("<h1 style='text-align:center; color:#1e3a8a; margin-bottom: 20px;'>⚽ World Cup 2026 Contest</h1>", unsafe_allow_html=True)

# NICKNAME CENTRATO
c_space1, c_nick, c_space2 = st.columns([1, 1, 1])
with c_nick:
    user = st.text_input("Inserisci Nickname Partecipante:", placeholder="Es. Marco_88")

# LOGIN ADMIN A DESTRA
with st.sidebar:
    st.write("### 🔒 Login Admin")
    admin_pw = st.text_input("Password", type="password")
    is_admin = (admin_pw == "mondiali2026")

if user:
    tab_list = ["🏟️ 1. Gironi", "📊 2. Classifiche", "🎾 3. Bracket (Wimbledon)", "🚀 4. Invia Pronostici"]
    if is_admin: tab_list.append("👑 ADMIN PANEL")
    tabs = st.tabs(tab_list)

    # --- TAB 1: GIRONI ---
    with tabs[0]:
        col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 1])
        with col_btn2:
            def auto_compila_utente():
                for i in range(72):
                    st.session_state[f"h_{i}"] = random.randint(0, 3)
                    st.session_state[f"a_{i}"] = random.randint(0, 3)
            st.button("🪄 Autocompila Tutti i Gironi", on_click=auto_compila_utente, use_container_width=True)

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
                            st.markdown(f"<div style='text-align:center;'><span class='badge-pts'>1: {p1}pt</span><span class='badge-pts'>X: {px}pt</span><span class='badge-pts'>2: {p2}pt</span></div>", unsafe_allow_html=True)
                            st.markdown("<span class='badge-bonus'>🎯 +50 pt Risultato Esatto</span>", unsafe_allow_html=True)
                            
                            c1, in1, vs, in2, c2 = st.columns([1, 1.2, 0.3, 1.2, 1])
                            c1.image(get_flag(m['h']), width=35)
                            st.session_state[f"h_{idx}"] = in1.number_input("H", 0, 9, key=f"wid_h_{idx}", value=st.session_state.get(f"h_{idx}", 0), label_visibility="collapsed")
                            vs.markdown("<p style='text-align:center; padding-top:10px; font-weight:800;'>-</p>", unsafe_allow_html=True)
                            st.session_state[f"a_{idx}"] = in2.number_input("A", 0, 9, key=f"wid_a_{idx}", value=st.session_state.get(f"a_{idx}", 0), label_visibility="collapsed")
                            c2.image(get_flag(m['a']), width=35)
                            st.markdown(f"<p style='text-align:center; font-size:12px; font-weight:700; margin-top:5px;'>{m['h']} vs {m['a']}</p>", unsafe_allow_html=True)

    # --- TAB 2: CLASSIFICHE ---
    with tabs[1]:
        st.write("### Situazione Classifiche (Aggiornamento in tempo reale)")
        r_usr, t3_usr, stats_usr = calcola_classifiche(prefisso="")
        for i in range(0, 12, 3):
            cs = st.columns(3)
            for k in range(3):
                gid = list(G_TEAMS.keys())[i+k]
                df = pd.DataFrame(stats_usr[gid]).T.sort_values(["Pt", "DR", "GF"], ascending=False)
                cs[k].write(f"**Gruppo {gid}**")
                cs[k].dataframe(df, use_container_width=True)

    # --- TAB 3: BRACKET WIMBLEDON ---
    def render_wimbledon_bracket(prefisso=""):
        ranks, terze, _ = calcola_classifiche(prefisso)
        
        def safe_team(gruppo, pos):
            try: return ranks[gruppo][pos]
            except: return "In attesa..."
            
        def match_tennis(t1, t2, mid):
            st.markdown("<div class='bracket-match'>", unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            with col1:
                st.image(get_flag(t1), width=30)
                if st.button(f"{t1}", key=f"b1_{prefisso}{mid}", use_container_width=True, type="primary" if st.session_state.get(prefisso+mid)==t1 else "secondary"):
                    st.session_state[prefisso+mid] = t1; st.rerun()
            with col2:
                st.image(get_flag(t2), width=30)
                if st.button(f"{t2}", key=f"b2_{prefisso}{mid}", use_container_width=True, type="primary" if st.session_state.get(prefisso+mid)==t2 else "secondary"):
                    st.session_state[prefisso+mid] = t2; st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
            return st.session_state.get(prefisso+mid, "In attesa...")

        c_sed, c_ott, c_qua, c_sem, c_fin = st.columns(5)
        
        with c_sed:
            st.markdown("<h4 style='color:#64748b;'>Sedicesimi</h4>", unsafe_allow_html=True)
            v_s1 = match_tennis(safe_team("A", 1), safe_team("C", 1), "S1")
            v_s2 = match_tennis(safe_team("D", 0), terze.get("A", "Miglior 3a"), "S2")
            v_s3 = match_tennis(safe_team("B", 0), terze.get("B", "Miglior 3a"), "S3")
            v_s4 = match_tennis(safe_team("F", 0), safe_team("E", 1), "S4")

        with c_ott:
            st.markdown("<h4 style='color:#64748b;'>Ottavi</h4><br>", unsafe_allow_html=True)
            v_o1 = match_tennis(v_s1, v_s2, "O1")
            st.write("<br>", unsafe_allow_html=True)
            v_o2 = match_tennis(v_s3, v_s4, "O2")

        with c_qua:
            st.markdown("<h4 style='color:#64748b;'>Quarti</h4><br><br><br>", unsafe_allow_html=True)
            v_q1 = match_tennis(v_o1, v_o2, "Q1")

        with c_sem:
            st.markdown("<h4 style='color:#64748b;'>Semifinali</h4><br><br><br><br><br>", unsafe_allow_html=True)
            v_semi = match_tennis(v_q1, "Altra Semifinalista", "Semi1")

        with c_fin:
            st.markdown("<h4 style='color:#1d4ed8;'>FINALE</h4><br><br><br><br><br><br>", unsafe_allow_html=True)
            campione = match_tennis(v_semi, "Finalista 2", "Winner")
            st.session_state[prefisso+"vincitore"] = campione
            if campione not in ["In attesa...", "Altra Semifinalista", "Finalista 2"] and prefisso=="": st.balloons()

    with tabs[2]:
        st.info("I nomi delle squadre appariranno non appena avrai compilato i risultati dei gironi.")
        render_wimbledon_bracket(prefisso="")

    # --- TAB 5: ADMIN PANEL (Visibile solo se loggato) ---
    if is_admin:
        with tabs[-1]:
            st.header("👑 Pannello di Controllo Admin")
            adm_tabs = st.tabs(["🏆 1. Classifica Ranking Partecipanti", "🏟️ 2. Risultati Reali", "⚔️ 3. Bracket Reale"])
            
            # SOTTO-TAB 1: CLASSIFICA
            with adm_tabs[0]:
                st.write("### Classifica Punti")
                st.info("Questa è la classifica ufficiale. Qui il sistema calcolerà i punti confrontando i pronostici salvati con i risultati reali che inserisci nelle schede successive.")
                # Struttura finta per mostrare dove andrà la classifica reale
                df_ranking = pd.DataFrame([{"Posizione": 1, "Utente": "Marco_88", "Punti": 185, "Bonus Esatti": 2}, {"Posizione": 2, "Utente": "Luca_Contest", "Punti": 140, "Bonus Esatti": 0}])
                st.dataframe(df_ranking, use_container_width=True)

            # SOTTO-TAB 2: RISULTATI
            with adm_tabs[1]:
                def auto_compila_admin():
                    for i in range(72):
                        st.session_state[f"adm_h_{i}"] = random.randint(0, 3)
                        st.session_state[f"adm_a_{i}"] = random.randint(0, 3)
                st.button("🪄 Autocompila Risultati Ufficiali (Per Test)", on_click=auto_compila_admin)
                
                for i, m in enumerate(MATCHES):
                    with st.expander(f"Girone {m['gr']} - {m['h']} vs {m['a']}"):
                        ca1, ca2 = st.columns(2)
                        st.session_state[f"adm_h_{i}"] = ca1.number_input(f"Gol {m['h']}", 0, 9, key=f"adm_w_h_{i}", value=st.session_state.get(f"adm_h_{i}", 0))
                        st.session_state[f"adm_a_{i}"] = ca2.number_input(f"Gol {m['a']}", 0, 9, key=f"adm_w_a_{i}", value=st.session_state.get(f"adm_a_{i}", 0))

            # SOTTO-TAB 3: BRACKET ADMIN
            with adm_tabs[2]:
                st.write("### Tabellone Ufficiale del Torneo")
                render_wimbledon_bracket(prefisso="adm_")
                st.divider()
                if st.button("💾 SALVA RISULTATI REALI NEL DATABASE", type="primary"):
                    payload_adm = {i: [st.session_state.get(f"adm_h_{i}"), st.session_state.get(f"adm_a_{i}")] for i in range(72)}
                    invia_google_sheets("RisultatiReali", "ADMIN", payload_adm)

    # --- TAB 4: INVIO ---
    with tabs[3]:
        st.write("### 🚀 Finito?")
        if st.button("INVIA I MIEI PRONOSTICI A GOOGLE SHEETS", type="primary", use_container_width=True):
            payload_user = {i: [st.session_state.get(f"h_{i}"), st.session_state.get(f"a_{i}")] for i in range(72)}
            if invia_google_sheets("Pronostici", user, {"Gironi": payload_user, "Vincitore": st.session_state.get("vincitore")}):
                st.success("Tutto inviato correttamente! In bocca al lupo!")
