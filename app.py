import streamlit as st
import pandas as pd
import json
import gspread
import random
import time
import urllib.parse
from google.oauth2.service_account import Credentials

# --- 1. CONFIGURAZIONE E GRAFICA ---
st.set_page_config(page_title="WC 2026 Contest", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800;900&display=swap');
    
    /* Global Styles */
    .stApp { background-color: #f8fafc; color: #0f172a; font-family: 'Inter', sans-serif; }
    
    /* Custom Header Landing Page */
    .hero-header {
        text-align: center; padding: 2rem 0 1rem 0;
    }
    .hero-title {
        font-size: 3.5rem; font-weight: 900; margin-bottom: 0;
        background: linear-gradient(90deg, #0ea5e9, #2563eb);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }
    .hero-subtitle {
        color: #64748b; font-size: 1.2rem; font-weight: 600; letter-spacing: 1px;
    }

    /* Tabs Styling */
    button[data-baseweb="tab"] p { font-size: 17px !important; font-weight: 700 !important; color: #64748b !important; }
    button[data-baseweb="tab"][aria-selected="true"] p { color: #2563eb !important; }

    /* Match Containers & Inputs */
    .stElementContainer div[data-testid="stVerticalBlockBorderControl"] {
        background-color: #ffffff !important; border: 1px solid #e2e8f0 !important; 
        border-radius: 12px !important; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05) !important;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .stElementContainer div[data-testid="stVerticalBlockBorderControl"]:hover {
        box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1) !important;
    }
    
    input[type="number"], input[type="text"] {
        background-color: #f1f5f9 !important; color: #0f172a !important;
        font-size: 20px !important; font-weight: 800 !important; border: 1px solid #cbd5e1 !important;
        border-radius: 8px !important; text-align: center !important; height: 45px !important;
        transition: all 0.2s ease;
    }
    input[type="number"]:focus, input[type="text"]:focus {
        border-color: #3b82f6 !important; box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.2) !important;
    }
    
    /* Login Admin: INVISIBILE E DISCRETO AL MASSIMO */
    .admin-login-wrapper {
        position: absolute; top: 0; right: 0; z-index: 999;
    }
    .admin-login-wrapper input {
        width: 15px !important; height: 15px !important; opacity: 0; border: none !important;
        background: transparent !important; padding: 0 !important; cursor: default;
        transition: all 0.3s ease;
    }
    .admin-login-wrapper input:focus {
        width: 150px !important; height: 35px !important; opacity: 1; cursor: text;
        background: #ffffff !important; font-size: 12px !important; color: #475569 !important;
        border: 1px solid #cbd5e1 !important; margin-top: 10px; margin-right: 10px;
    }
    
    /* Labels & Badges */
    .pts-badge { background: #e0f2fe; color: #0369a1; padding: 4px 8px; border-radius: 6px; font-size: 11px; font-weight: 800; border: 1px solid #bae6fd; margin: 0 3px; }
    .bonus-txt { color: #dc2626; font-size: 11px; font-weight: 800; display: block; text-align: center; margin-top: 8px; }
    
    .admin-match-box { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 10px; margin-bottom: 12px; }
    .admin-match-title { font-size: 13px; font-weight: 800; text-align: center; color: #475569; margin-bottom: 8px; }
    
    /* Premium Bracket Styling */
    div.stButton > button {
        border-radius: 8px; font-weight: 700; border: 1px solid #e2e8f0;
        background-color: #f8fafc; color: #475569; transition: all 0.2s ease;
    }
    div.stButton > button:hover {
        border-color: #93c5fd; color: #2563eb; background-color: #eff6ff;
    }
    div.stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #0284c7 0%, #2563eb 100%) !important;
        border: none !important; color: white !important; font-weight: 800 !important;
        box-shadow: 0 4px 10px rgba(37, 99, 235, 0.3) !important;
    }
    .bracket-round-title {
        font-size: 12px; font-weight: 900; text-transform: uppercase; letter-spacing: 1.5px;
        color: #ffffff; background-color: #1e293b; padding: 6px 12px; border-radius: 20px;
        text-align: center; margin-bottom: 20px; display: inline-block;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. INIZIALIZZAZIONE MEMORIA (ANTI-CRASH) ---
if "initialized" not in st.session_state:
    for i in range(72):
        st.session_state[f"h_{i}"] = 0
        st.session_state[f"a_{i}"] = 0
        st.session_state[f"adm_h_{i}"] = None  
        st.session_state[f"adm_a_{i}"] = None  
    for k in [f"S{i}" for i in range(1,17)] + [f"O{i}" for i in range(1,9)] + [f"Q{i}" for i in range(1,5)] + ["SEM1", "SEM2", "WINNER"]:
        st.session_state[k] = "TBD"
        st.session_state[f"adm_{k}"] = "TBD"
    st.session_state["initialized"] = True

if "admin_force_blank" not in st.session_state:
    for i in range(72):
        if st.session_state.get(f"adm_h_{i}") == 0: st.session_state[f"adm_h_{i}"] = None
        if st.session_state.get(f"adm_a_{i}") == 0: st.session_state[f"adm_a_{i}"] = None
    st.session_state["admin_force_blank"] = True

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

# --- 4. CONNESSIONE GOOGLE SHEETS & MOTORE RANKING CORAZZATO ---
def get_gspread_client():
    conf = json.loads(st.secrets["service_account"])
    creds = Credentials.from_service_account_info(conf, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
    return gspread.authorize(creds)

# ⚠️ INSERISCI QUI IL TUO ID DEL FOGLIO ⚠️
ID_DEL_FOGLIO = "1palUSBw4IlBFzU4dKtgT0tnjPiPEtxIc6K-DK05vXG8" 

def invia_google_sheets(tab_name, nick, dati):
    try:
        gc = get_gspread_client()
        sh = gc.open_by_key(ID_DEL_FOGLIO)
        try: ws = sh.worksheet(tab_name)
        except: ws = sh.add_worksheet(title=tab_name, rows="1", cols="5")
        ws.append_row([nick, json.dumps(dati)])
        return True
    except Exception as e:
        st.error(f"❌ ERRORE: Impossibile scrivere sul file. Verifica le API.")
        return False

def safe_json_parse(val):
    try: return json.loads(val)
    except: return {}

def force_int(val):
    try:
        if val is None: return None
        s = str(val).strip().lower()
        if s == "" or s == "none" or s == "null": return None
        return int(float(s))
    except:
        return None

def get_admin_dashboard_data():
    try:
        gc = get_gspread_client()
        sh = gc.open_by_key(ID_DEL_FOGLIO)
        
        try: ws_pro = sh.worksheet("Pronostici")
        except: return pd.DataFrame(), [], None
        
        try: ws_real = sh.worksheet("RisultatiReali")
        except: ws_real = None
        
        dati_utenti = ws_pro.get_all_values()
        if not dati_utenti: return pd.DataFrame(), [], ws_pro
        
        reali_dict = {}
        if ws_real:
            dati_reali = ws_real.get_all_values()
            for row in reversed(dati_reali):
                if len(row) >= 2:
                    data = safe_json_parse(row[1])
                    if isinstance(data, dict):
                        if "Gironi" in data:
                            reali_dict = data["Gironi"]
                            break
                        elif any(k.startswith("G_") or str(k).isdigit() for k in data.keys()):
                            reali_dict = data
                            break

        classifica = []
        nomi_utenti = []
        
        for idx, row in enumerate(dati_utenti):
            if len(row) < 2: continue
            
            nick = row[0]
            user_data = safe_json_parse(row[1])
            if not isinstance(user_data, dict): continue
            
            nomi_utenti.append((nick, idx + 1))
            
            user_gironi = user_data.get("Gironi", user_data)
            if not isinstance(user_gironi, dict): continue
            
            punti_tot = 0
            punti_bonus = 0
            
            for i, m in enumerate(MATCHES):
                key_str = f"G_{m['gr']} {m['h']}-{m['a']}"
                key_num = str(i)
                
                r_vals = reali_dict.get(key_str, reali_dict.get(key_num))
                
                if isinstance(r_vals, list) and len(r_vals) >= 2:
                    r_h = force_int(r_vals[0])
                    r_a = force_int(r_vals[1])
                    
                    if r_h is not None and r_a is not None:
                        u_vals = user_gironi.get(key_str, user_gironi.get(key_num))
                        
                        u_h, u_a = 0, 0 
                        if isinstance(u_vals, list) and len(u_vals) >= 2:
                            uh_f = force_int(u_vals[0])
                            ua_f = force_int(u_vals[1])
                            if uh_f is not None: u_h = uh_f
                            if ua_f is not None: u_a = ua_f
                            
                        u_esito = 1 if u_h > u_a else (2 if u_a > u_h else 0)
                        r_esito = 1 if r_h > r_a else (2 if r_a > r_h else 0)
                        
                        p1 = RANKING.get(m['h'], 0)
                        p2 = RANKING.get(m['a'], 0)
                        px = (p1 + p2) // 2
                        
                        if u_esito == r_esito:
                            if r_esito == 1: punti_tot += p1
                            elif r_esito == 2: punti_tot += p2
                            else: punti_tot += px
                            
                        if u_h == r_h and u_a == r_a:
                            punti_tot += 50
                            punti_bonus += 50
                            
            classifica.append({"Partecipante": nick, "Punti Totali": punti_tot, "Bonus Esatti": punti_bonus})
            
        df = pd.DataFrame(classifica)
        if not df.empty:
            df = df.groupby('Partecipante', as_index=False).last()
            df = df.sort_values(by=["Punti Totali", "Bonus Esatti"], ascending=[False, False]).reset_index(drop=True)
            df.index += 1
        return df, nomi_utenti, ws_pro
    except Exception as e:
        return pd.DataFrame(), [], None

def elimina_utente(ws, row_index):
    try: ws.delete_row(int(row_index))
    except:
        try: ws.delete_rows(int(row_index))
        except: return False
    return True

# --- 5. CALCOLI CLASSIFICHE GIRONI (UI) ---
def calcola_classifiche(prefisso=""):
    stats = {g: {t: {"Pt": 0, "DR": 0, "GF": 0} for t in ts} for g, ts in G_TEAMS.items()}
    for i, m in enumerate(MATCHES):
        h = st.session_state[f"{prefisso}h_{i}"]
        a = st.session_state[f"{prefisso}a_{i}"]
        
        if h is None or a is None or str(h).strip() == "" or str(a).strip() == "":
            continue
            
        h, a = int(h), int(a)
        
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

# --- 6. INTERFACCIA MAIN ---

# Admin Invisibile
st.markdown("<div class='admin-login-wrapper'>", unsafe_allow_html=True)
admin_pw = st.text_input(" ", type="password", key="admin_auth", label_visibility="collapsed")
is_admin = (admin_pw == "mondiali2026")
st.markdown("</div>", unsafe_allow_html=True)

# Intestazione Premium
st.markdown("""
<div class='hero-header'>
    <h1 class='hero-title'>🏆 WC 2026 Contest</h1>
    <p class='hero-subtitle'>Pronostica. Sfida. Domina.</p>
</div>
""", unsafe_allow_html=True)

user = ""

# Layout Landing Page se non c'è admin e non c'è utente
if not is_admin:
    st.write("<br><br>", unsafe_allow_html=True)
    c_space1, c_nick, c_space2 = st.columns([1, 1.5, 1])
    with c_nick:
        st.markdown("<h4 style='text-align:center; color:#334155; margin-bottom: 15px;'>Inserisci il tuo Nickname per iniziare</h4>", unsafe_allow_html=True)
        user = st.text_input("Nickname:", placeholder="Es. Marco_88", label_visibility="collapsed")
        
        if not user:
            st.info("💡 Attenzione: Scegli un nome riconoscibile. Tutti i tuoi pronostici verranno salvati su di esso.")

if user or is_admin:
    
    tab_list = ["🏟️ Gironi", "📊 Classifiche", "🎾 Bracket Completo"]
    if user: tab_list.append("🚀 Invia Pronostici")
    if is_admin: tab_list.append("👑 Pannello Admin")
    
    tabs = st.tabs(tab_list)

    # --- TAB GIRONI ---
    with tabs[0]:
        c_btn1, c_btn2, c_btn3 = st.columns([1, 1.5, 1])
        with c_btn2:
            st.write("<br>", unsafe_allow_html=True)
            if st.button("🪄 Autocompila Gironi Casualmente", use_container_width=True):
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
                            vs.markdown("<p style='text-align:center; padding-top:6px; font-weight:900; color:#cbd5e1;'>-</p>", unsafe_allow_html=True)
                            in2.number_input("A", min_value=0, max_value=9, key=f"a_{idx}", label_visibility="collapsed")
                            c2.image(get_flag(m['a']), width=30)
                            st.markdown(f"<p style='text-align:center; font-size:13px; font-weight:700; margin-top:8px; color:#334155;'>{m['h']} v {m['a']}</p>", unsafe_allow_html=True)

    # --- TAB CLASSIFICHE ---
    with tabs[1]:
        r_usr, t3_usr, stats_usr = calcola_classifiche(prefisso="")
        for i in range(0, 12, 3):
            cs = st.columns(3)
            for k in range(3):
                gid = list(G_TEAMS.keys())[i+k]
                df = pd.DataFrame(stats_usr[gid]).T.sort_values(["Pt", "DR", "GF"], ascending=False)
                cs[k].markdown(f"<h4 style='color:#1e293b;'>Gruppo {gid}</h4>", unsafe_allow_html=True)
                cs[k].dataframe(df, use_container_width=True)

    # --- TAB BRACKET ALGORITMICO "TENNISTICO" ---
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
                st.markdown(f"<div style='font-size:10px; color:#94a3b8; font-weight:800; text-align:center; margin-bottom:5px;'>MATCH {mid}</div>", unsafe_allow_html=True)
                if st.button(t1, key=f"btn1_{prefisso}{mid}", use_container_width=True, type="primary" if st.session_state[prefisso+mid]==t1 else "secondary"):
                    st.session_state[prefisso+mid]=t1; st.rerun()
                if st.button(t2, key=f"btn2_{prefisso}{mid}", use_container_width=True, type="primary" if st.session_state[prefisso+mid]==t2 else "secondary"):
                    st.session_state[prefisso+mid]=t2; st.rerun()
            return st.session_state[prefisso+mid]

        st.info("🎾 **Bracket Mode:** Clicca sul nome della squadra vincitrice in ogni riquadro per farla avanzare nel tabellone.")
        c_sed, c_ott, c_qua, c_sem, c_fin = st.columns(5)
        
        # Algoritmo distanziale matematico per allineamento simmetrico
        BH = 110
        def space(n):
            if n > 0: st.markdown(f"<div style='height:{int(n*BH)}px'></div>", unsafe_allow_html=True)

        with c_sed:
            st.markdown("<div style='text-align:center;'><span class='bracket-round-title'>Sedicesimi</span></div>", unsafe_allow_html=True)
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
            st.markdown("<div style='text-align:center;'><span class='bracket-round-title'>Ottavi</span></div>", unsafe_allow_html=True)
            space(0.5)
            o1 = t_box(s1, s2, "O1")
            space(1)
            o2 = t_box(s3, s4, "O2")
            space(1)
            o3 = t_box(s5, s6, "O3")
            space(1)
            o4 = t_box(s7, s8, "O4")
            space(1)
            o5 = t_box(s9, s10, "O5")
            space(1)
            o6 = t_box(s11, s12, "O6")
            space(1)
            o7 = t_box(s13, s14, "O7")
            space(1)
            o8 = t_box(s15, s16, "O8")

        with c_qua:
            st.markdown("<div style='text-align:center;'><span class='bracket-round-title'>Quarti</span></div>", unsafe_allow_html=True)
            space(1.5)
            q1 = t_box(o1, o2, "Q1")
            space(3)
            q2 = t_box(o3, o4, "Q2")
            space(3)
            q3 = t_box(o5, o6, "Q3")
            space(3)
            q4 = t_box(o7, o8, "Q4")

        with c_sem:
            st.markdown("<div style='text-align:center;'><span class='bracket-round-title'>Semi</span></div>", unsafe_allow_html=True)
            space(3.5)
            sem1 = t_box(q1, q2, "SEM1")
            space(7)
            sem2 = t_box(q3, q4, "SEM2")

        with c_fin:
            st.markdown("<div style='text-align:center;'><span class='bracket-round-title' style='background-color:#0284c7;'>🏆 FINALE</span></div>", unsafe_allow_html=True)
            space(7.5)
            vinc_key = "adm_vincitore" if prefisso == "adm_" else "WINNER"
            win = t_box(sem1, sem2, "WINNER")
            st.session_state[vinc_key] = win

    with tabs[2]:
        render_wimbledon(prefisso="")

    # --- INVIO UTENTE ---
    if user:
        with tabs[3]:
            st.write("### 🚀 Manda i Pronostici Ufficiali")
            st.write("Verifica di aver completato tutti i gironi e tutto il tabellone prima di procedere.")
            
            if st.session_state.get("user_saved_success"):
                st.success(f"✅ Ottimo lavoro {user}, i tuoi pronostici sono stati salvati!")
                st.session_state["user_saved_success"] = False

            st.write("<br>", unsafe_allow_html=True)
            if st.button("INVIA I TUOI PRONOSTICI DEFINITIVAMENTE", type="primary", use_container_width=True):
                payload_user = {f"G_{MATCHES[i]['gr']} {MATCHES[i]['h']}-{MATCHES[i]['a']}": [st.session_state[f"h_{i}"], st.session_state[f"a_{i}"]] for i in range(72)}
                chiavi_bracket = [f"S{i}" for i in range(1,17)] + [f"O{i}" for i in range(1,9)] + [f"Q{i}" for i in range(1,5)] + ["SEM1", "SEM2", "WINNER"]
                payload_bracket = {k: st.session_state[k] for k in chiavi_bracket}
                
                if invia_google_sheets("Pronostici", user, {"Gironi": payload_user, "Bracket": payload_bracket}):
                    st.session_state["user_saved_success"] = True
                    time.sleep(1) 
                    st.rerun()

    # --- ADMIN AREA ---
    if is_admin:
        with tabs[-1]:
            st.header("👑 Pannello Admin")
            
            if st.session_state.get("admin_saved_success"):
                st.success("✅ Risultati Reali e Tabellone salvati con successo! La classifica ufficiale è aggiornata.")
                st.session_state["admin_saved_success"] = False

            adm_tabs = st.tabs(["📊 Ranking Partecipanti", "⚽ Inserimento Risultati Reali", "🏆 Bracket Reale"])
            
            with adm_tabs[0]:
                st.write("### Classifica Ufficiale")
                st.info("⚠️ I punti vengono assegnati **solo** dopo aver inserito i risultati reali e cliccato il bottone 'Salva' blu in basso.")
                
                df_ranking, nomi_utenti, ws_pronostici = get_admin_dashboard_data()
                
                if not df_ranking.empty:
                    st.dataframe(df_ranking, use_container_width=True)
                    
                    st.write("<br>", unsafe_allow_html=True)
                    wa_text = "🏆 *CLASSIFICA MONDIALE 2026* 🏆\n\n"
                    for i, r in df_ranking.iterrows():
                        wa_text += f"*{i}. {r['Partecipante']}* - {r['Punti Totali']} pt (Bonus: {r['Bonus Esatti']})\n"
                    wa_text += "\n⚽ Generato dalla Master App!"
                    wa_url = f"https://api.whatsapp.com/send?text={urllib.parse.quote(wa_text)}"
                    
                    c_wa1, c_wa2, c_wa3 = st.columns([1, 2, 1])
                    with c_wa2:
                        st.markdown(f"""
                        <a href="{wa_url}" target="_blank" style="text-decoration:none; display:flex; justify-content:center;">
                            <div style="background-color:#25D366; color:white; padding:12px 24px; border-radius:8px; text-align:center; font-weight:800; width:100%; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 20px;">
                                💬 Condividi Classifica su WhatsApp
                            </div>
                        </a>
                        """, unsafe_allow_html=True)
                    
                    st.divider()
                    st.write("#### Gestione Utenti")
                    if nomi_utenti:
                        col_del1, col_del2 = st.columns([2, 1])
                        with col_del1:
                            utente_da_eliminare = st.selectbox("Seleziona Partecipante da eliminare", options=nomi_utenti, format_func=lambda x: f"{x[0]} (Riga Foglio: {x[1]})")
                        with col_del2:
                            st.write("<br>", unsafe_allow_html=True)
                            if st.button("🗑️ Elimina Utente", type="primary"):
                                if utente_da_eliminare and elimina_utente(ws_pronostici, utente_da_eliminare[1]):
                                    st.success(f"{utente_da_eliminare[0]} eliminato! Ricaricamento in corso...")
                                    st.rerun() 
                                else:
                                    st.error("Errore durante l'eliminazione.")
                else:
                    st.warning("Nessun partecipante o nessun risultato salvato per calcolare i punti.")

            with adm_tabs[1]:
                col_btn_test, _ = st.columns([1, 2])
                with col_btn_test:
                    if st.button("🪄 Autocompila Reali (Test)"):
                        for i in range(72):
                            st.session_state[f"adm_h_{i}"] = random.randint(0, 3)
                            st.session_state[f"adm_a_{i}"] = random.randint(0, 3)
                        st.rerun()
                
                # CORREZIONE: reinserito il parametro value=None per garantire input completamente vuoti
                for r in range(18):
                    cols = st.columns(4)
                    for c in range(4):
                        idx = r * 4 + c
                        if idx < 72:
                            m = MATCHES[idx]
                            with cols[c]:
                                st.markdown(f"<div class='admin-match-box'><div class='admin-match-title'>G{m['gr']} {m['h']} - {m['a']}</div>", unsafe_allow_html=True)
                                ci1, ci2 = st.columns(2)
                                ci1.number_input("H", min_value=0, max_value=9, value=None, key=f"adm_h_{idx}", label_visibility="collapsed")
                                ci2.number_input("A", min_value=0, max_value=9, value=None, key=f"adm_a_{idx}", label_visibility="collapsed")
                                st.markdown("</div>", unsafe_allow_html=True)
                        
            with adm_tabs[2]:
                render_wimbledon(prefisso="adm_")
                
            st.divider()
            if st.button("💾 SALVA TUTTO (RISULTATI E TABELLONE) IN GOOGLE SHEETS", type="primary", use_container_width=True):
                payload_adm = {f"G_{MATCHES[i]['gr']} {MATCHES[i]['h']}-{MATCHES[i]['a']}": [st.session_state.get(f"adm_h_{i}"), st.session_state.get(f"adm_a_{i}")] for i in range(72)}
                chiavi_bracket_adm = [f"adm_{k}" for k in [f"S{i}" for i in range(1,17)] + [f"O{i}" for i in range(1,9)] + [f"Q{i}" for i in range(1,5)] + ["SEM1", "SEM2", "WINNER"]]
                payload_adm_bracket = {k.replace("adm_", ""): st.session_state[k] for k in chiavi_bracket_adm}
                
                if invia_google_sheets("RisultatiReali", "ADMIN", {"Gironi": payload_adm, "Bracket": payload_adm_bracket}):
                    st.session_state["admin_saved_success"] = True
                    time.sleep(1) 
                    st.rerun()
