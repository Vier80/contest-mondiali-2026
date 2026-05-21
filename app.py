import streamlit as st
import pandas as pd
import json
import gspread
import random
import time
import urllib.parse
import base64
from google.oauth2.service_account import Credentials

try:
    from fpdf import FPDF
    HAS_FPDF = True
except ImportError:
    HAS_FPDF = False

# --- 1. CONFIGURAZIONE E GRAFICA (TEMA FIFA 2026) ---
st.set_page_config(
    page_title="FIFA World Cup 2026 Contest", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800;900&display=swap');
    
    .stApp { 
        background-color: #000000; 
        color: #f8fafc; 
        font-family: 'Inter', sans-serif; 
    }
    
    .hero-header { 
        text-align: center; 
        padding: 1rem 0 1rem 0; 
    }
    
    .hero-title {
        font-size: 3.5rem; 
        font-weight: 900; 
        margin-bottom: 0;
        background: linear-gradient(90deg, #00ff87, #60efff, #3b82f6);
        -webkit-background-clip: text; 
        -webkit-text-fill-color: transparent;
    }
    
    .hero-subtitle { 
        color: #cbd5e1; 
        font-size: 1.2rem; 
        font-weight: 600; 
        letter-spacing: 1px; 
    }

    button[data-baseweb="tab"] p { 
        font-size: 16px !important; 
        font-weight: 700 !important; 
        color: #94a3b8 !important; 
    }
    
    button[data-baseweb="tab"][aria-selected="true"] p { 
        color: #00ff87 !important; 
    }

    .stElementContainer div[data-testid="stVerticalBlockBorderControl"] {
        background-color: #1a1a1a !important; 
        border: 1px solid #444444 !important; 
        border-radius: 12px !important; 
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.5) !important;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    
    .stElementContainer div[data-testid="stVerticalBlockBorderControl"]:hover {
        border-color: #60efff !important; 
        box-shadow: 0 0 15px rgba(96, 239, 255, 0.4) !important;
    }
    
    input[type="number"], input[type="text"] {
        background-color: #2a2a2a !important; 
        color: #ffffff !important;
        font-size: 20px !important; 
        font-weight: 800 !important; 
        border: 1px solid #444444 !important;
        border-radius: 8px !important; 
        text-align: center !important; 
        height: 45px !important;
    }
    
    input[type="number"]:focus, input[type="text"]:focus {
        border-color: #00ff87 !important; 
        box-shadow: 0 0 0 3px rgba(0, 255, 135, 0.2) !important;
    }
    
    input[type="password"] { 
        font-size: 14px !important; 
        height: 35px !important; 
    }
    
    .pts-badge { 
        background: #2a2a2a; 
        color: #60efff; 
        padding: 4px 8px; 
        border-radius: 6px; 
        font-size: 11px; 
        font-weight: 800; 
        border: 1px solid #444444; 
        margin: 0 3px; 
    }
    
    .bonus-txt { 
        color: #00ff87; 
        font-size: 11px; 
        font-weight: 800; 
        display: block; 
        text-align: center; 
        margin-top: 8px; 
        margin-bottom: 8px; 
    }
    
    .admin-match-box { 
        background: #1a1a1a; 
        border: 1px solid #444444; 
        border-radius: 8px; 
        padding: 10px; 
        margin-bottom: 12px; 
        color: white;
    }
    
    .admin-match-title { 
        font-size: 13px; 
        font-weight: 800; 
        text-align: center; 
        color: #e2e8f0; 
        margin-bottom: 8px; 
    }
    
    div.stButton > button {
        border-radius: 8px; 
        font-weight: 700; 
        border: 1px solid #444444;
        background-color: #2a2a2a; 
        color: #ffffff; 
        margin-bottom: 0px !important;
    }
    
    div.stButton > button:hover { 
        border-color: #60efff; 
        color: #ffffff; 
        background-color: #3a3a3a; 
    }
    
    div.stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #00ff87 0%, #3b82f6 100%) !important;
        border: none !important; 
        color: #000 !important; 
        font-weight: 800 !important;
        box-shadow: 0 4px 10px rgba(0, 255, 135, 0.3) !important;
    }
    
    .bracket-round-title {
        font-size: 11px; 
        font-weight: 900; 
        text-transform: uppercase; 
        letter-spacing: 1px;
        color: #000; 
        background: #00ff87; 
        padding: 4px 8px; 
        border-radius: 20px;
        text-align: center; 
        display: inline-block; 
        border: 1px solid #00ff87; 
        margin-bottom: 10px;
    }

    div[data-testid="stHorizontalBlock"]:has(.bracket-round-title) { 
        align-items: stretch !important; 
    }
    
    /* LOGIN ADMIN SEGRETO */
    div[data-testid="stTextInput"]:has(input[type="password"]) {
        width: 40px; 
        margin: 150px auto 0 auto; 
        opacity: 0; 
        transition: all 0.4s ease;
    }
    
    div[data-testid="stTextInput"]:has(input[type="password"]):hover,
    div[data-testid="stTextInput"]:has(input[type="password"]):focus-within {
        opacity: 1; 
        width: 200px;
    }
    
    input[type="password"]::placeholder { 
        color: #444444 !important; 
        text-align: center; 
        font-weight: 900; 
        font-size: 18px; 
    }
    
    @media (max-width: 768px) {
        .hero-title { font-size: 2.2rem !important; }
        .hero-subtitle { font-size: 1rem !important; }
        div[data-testid="stVerticalBlockBorderControl"] { padding: 10px !important; }
        input[type="number"], input[type="text"] { font-size: 16px !important; height: 38px !important; }
        div.stButton > button { font-size: 12px !important; padding: 2px 5px !important; min-height: 35px !important; }
    }
</style>
""", unsafe_allow_html=True)

# --- 2. INIZIALIZZAZIONE MEMORIA E GESTIONE ADMIN ---
if "initialized" not in st.session_state:
    for i in range(72):
        st.session_state[f"h_{i}"] = 0
        st.session_state[f"a_{i}"] = 0
        st.session_state[f"adm_h_{i}"] = None
        st.session_state[f"adm_a_{i}"] = None  
        
    for k in [f"S{i}" for i in range(1,17)] + [f"O{i}" for i in range(1,9)] + [f"Q{i}" for i in range(1,5)] + ["SEM1", "SEM2", "THIRD", "WINNER"]:
        st.session_state[k] = "TBD"
        st.session_state[f"adm_{k}"] = "TBD"
        
    st.session_state["top_scorer"] = ""
    st.session_state["adm_top_scorer"] = ""
    st.session_state["initialized"] = True

if "admin_force_blank" not in st.session_state:
    for i in range(72):
        if st.session_state.get(f"adm_h_{i}") == 0: 
            st.session_state[f"adm_h_{i}"] = None
        if st.session_state.get(f"adm_a_{i}") == 0: 
            st.session_state[f"adm_a_{i}"] = None
    st.session_state["admin_force_blank"] = True

if "current_user" not in st.session_state: 
    st.session_state["current_user"] = ""

if "is_admin" not in st.session_state: 
    st.session_state["is_admin"] = False

if st.session_state.get("admin_auth") == "mondiali2026": 
    st.session_state["is_admin"] = True

is_admin = st.session_state["is_admin"]

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
    "A": ["Messico", "Sudafrica", "Sudcorea", "Repubblica Ceca"], 
    "B": ["Canada", "Bosnia Erzegovina", "Qatar", "Svizzera"],
    "C": ["Brasile", "Marocco", "Haiti", "Scozia"], 
    "D": ["USA", "Paraguay", "Australia", "Turchia"],
    "E": ["Germania", "Curacao", "Costa D'Avorio", "Ecuador"], 
    "F": ["Olanda", "Giappone", "Svezia", "Tunisia"],
    "G": ["Belgio", "Egitto", "Iran", "Nuova Zelanda"], 
    "H": ["Spagna", "Capo Verde", "Arabia Saudita", "Uruguay"],
    "I": ["Francia", "Senegal", "Iraq", "Norvegia"], 
    "J": ["Argentina", "Algeria", "Austria", "Giordania"],
    "K": ["Portogallo", "DR Congo", "Uzbekistan", "Colombia"], 
    "L": ["Inghilterra", "Croazia", "Ghana", "Panama"]
}

MATCHES = []
for gid, teams in G_TEAMS.items():
    for h, a in [(0, 1), (2, 3), (0, 2), (1, 3), (0, 3), (1, 2)]: 
        MATCHES.append({"gr": gid, "h": teams[h], "a": teams[a]})
        
BRACKET_KEYS = [f"S{i}" for i in range(1,17)] + [f"O{i}" for i in range(1,9)] + [f"Q{i}" for i in range(1,5)] + ["SEM1", "SEM2", "THIRD", "WINNER"]

def get_flag(t):
    if not t or t in ["TBD", "In attesa..."]: 
        return "https://flagcdn.com/w160/un.png"
    m = {
        "Messico": "mx", "Sudafrica": "za", "Sudcorea": "kr", "Repubblica Ceca": "cz", 
        "Canada": "ca", "Bosnia Erzegovina": "ba", "Qatar": "qa", "Svizzera": "ch", 
        "Brasile": "br", "Marocco": "ma", "Haiti": "ht", "Scozia": "gb-sct", 
        "USA": "us", "Paraguay": "py", "Australia": "au", "Turchia": "tr", 
        "Germania": "de", "Curacao": "cw", "Costa D'Avorio": "ci", "Ecuador": "ec", 
        "Olanda": "nl", "Giappone": "jp", "Svezia": "se", "Tunisia": "tn", 
        "Belgio": "be", "Egitto": "eg", "Iran": "ir", "Nuova Zelanda": "nz", 
        "Spagna": "es", "Capo Verde": "cv", "Arabia Saudita": "sa", "Uruguay": "uy", 
        "Francia": "fr", "Senegal": "sn", "Iraq": "iq", "Norvegia": "no", 
        "Argentina": "ar", "Algeria": "dz", "Austria": "at", "Giordania": "jo", 
        "Portogallo": "pt", "DR Congo": "cd", "Uzbekistan": "uz", "Colombia": "co", 
        "Inghilterra": "gb-eng", "Croazia": "hr", "Ghana": "gh", "Panama": "pa", "Italia": "it"
    }
    return f"https://flagcdn.com/w160/{m.get(t, 'un')}.png"

# --- 4. CONNESSIONE E LOGICA ---
def get_gspread_client():
    conf = json.loads(st.secrets["service_account"])
    creds = Credentials.from_service_account_info(conf, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
    return gspread.authorize(creds)

# ⚠️ INSERISCI QUI IL TUO ID DEL FOGLIO ⚠️
ID_DEL_FOGLIO = "1palUSBw4IlBFzU4dKtgT0tnjPiPEtxIc6K-DK05vXG8" 

def safe_json_parse(val):
    try: 
        return json.loads(val)
    except: 
        return {}

def force_int(val):
    try:
        if val is None: 
            return None
        s = str(val).strip().lower()
        if s == "" or s == "none" or s == "null": 
            return None
        return int(float(s))
    except: 
        return None

def carica_dati_utente_da_sheets(nick):
    try:
        gc = get_gspread_client()
        sh = gc.open_by_key(ID_DEL_FOGLIO)
        
        try: ws = sh.worksheet("Pronostici")
        except: return False
            
        records = ws.get_all_values()
        for row in reversed(records):
            if len(row) >= 2 and row[0].strip().lower() == nick.strip().lower():
                data = safe_json_parse(row[1])
                if isinstance(data, dict):
                    gironi_data = data.get("Gironi", data)
                    bracket_data = data.get("Bracket", {})
                    st.session_state["top_scorer"] = data.get("TopScorer", "")
                    
                    for i, m in enumerate(MATCHES):
                        key_str = f"G_{m['gr']} {m['h']}-{m['a']}"
                        if isinstance(gironi_data, dict) and key_str in gironi_data:
                            vals = gironi_data[key_str]
                            if isinstance(vals, list) and len(vals) >= 2:
                                h_val = force_int(vals[0])
                                a_val = force_int(vals[1])
                                if h_val is not None: st.session_state[f"h_{i}"] = h_val
                                if a_val is not None: st.session_state[f"a_{i}"] = a_val
                                    
                    if isinstance(bracket_data, dict):
                        for k in BRACKET_KEYS:
                            if k in bracket_data: st.session_state[k] = bracket_data[k]
                    return True
        return False
    except: return False

def invia_google_sheets(tab_name, nick, dati):
    try:
        gc = get_gspread_client()
        sh = gc.open_by_key(ID_DEL_FOGLIO)
        try: ws = sh.worksheet(tab_name)
        except: ws = sh.add_worksheet(title=tab_name, rows="1", cols="5")
        ws.append_row([nick, json.dumps(dati)])
        return True
    except Exception: return False

def salva_dettaglio_punti_sheets(dettagli_list):
    if not dettagli_list: return "Nessun dato da salvare."
    try:
        gc = get_gspread_client()
        sh = gc.open_by_key(ID_DEL_FOGLIO)
        try: ws = sh.worksheet("DettaglioPunti")
        except: ws = sh.add_worksheet(title="DettaglioPunti", rows="1", cols="10")
        df_det = pd.DataFrame(dettagli_list).fillna(0)
        dati_matrice = [df_det.columns.tolist()] + df_det.astype(str).values.tolist()
        ws.clear()
        try: ws.update("A1", dati_matrice)
        except Exception as e1:
            try: ws.update(range_name="A1", values=dati_matrice)
            except Exception as e2: return "API Gspread bloccata."
        return "OK"
    except Exception as e: return f"Errore: {str(e)}"

def carica_dati_paracadute():
    try:
        gc = get_gspread_client()
        sh = gc.open_by_key(ID_DEL_FOGLIO)
        ws_real = sh.worksheet("RisultatiReali")
        dati_reali = ws_real.get_all_values()
        
        for row in reversed(dati_reali):
            if len(row) >= 2:
                data = safe_json_parse(row[1])
                if isinstance(data, dict):
                    gironi_data = data.get("Gironi", data)
                    bracket_data = data.get("Bracket", {})
                    st.session_state["adm_top_scorer"] = data.get("TopScorer", "")
                    
                    for i, m in enumerate(MATCHES):
                        key_str = f"G_{m['gr']} {m['h']}-{m['a']}"
                        if key_str in gironi_data:
                            st.session_state[f"adm_h_{i}"] = force_int(gironi_data[key_str][0])
                            st.session_state[f"adm_a_{i}"] = force_int(gironi_data[key_str][1])
                            
                    for k, v in bracket_data.items(): st.session_state[f"adm_{k}"] = v
                    break
    except Exception: pass

def get_32_qualifiers(gironi_dict):
    stats = {g: {t: {"Pt": 0, "DR": 0, "GF": 0, "Played": 0} for t in ts} for g, ts in G_TEAMS.items()}
    for i, m in enumerate(MATCHES):
        key_str = f"G_{m['gr']} {m['h']}-{m['a']}"
        key_num = str(i)
        vals = gironi_dict.get(key_str, gironi_dict.get(key_num))
        if isinstance(vals, list) and len(vals) >= 2:
            h = force_int(vals[0]); a = force_int(vals[1])
            if h is not None and a is not None:
                stats[m['gr']][m['h']]["GF"] += h
                stats[m['gr']][m['a']]["GF"] += a
                stats[m['gr']][m['h']]["DR"] += (h - a)
                stats[m['gr']][m['a']]["DR"] += (a - h)
                stats[m['gr']][m['h']]["Played"] += 1
                stats[m['gr']][m['a']]["Played"] += 1
                if h > a: stats[m['gr']][m['h']]["Pt"] += 3
                elif a > h: stats[m['gr']][m['a']]["Pt"] += 3
                else: stats[m['gr']][m['h']]["Pt"] += 1; stats[m['gr']][m['a']]["Pt"] += 1
                    
    rankings_finali = {}; terze_squadre = []
    for g, ts in stats.items():
        df = pd.DataFrame(ts).T
        if df["Played"].sum() == 0: rankings_finali[g] = []
        else:
            df = df.sort_values(["Pt", "DR", "GF"], ascending=False)
            rankings_finali[g] = df.index.tolist()
            terze_squadre.append({"Squadra": df.index[2], "Pt": df.iloc[2]["Pt"], "DR": df.iloc[2]["DR"]})
            
    terze_squadre_df = pd.DataFrame(terze_squadre)
    if not terze_squadre_df.empty:
        migliori_terze = terze_squadre_df.sort_values(["Pt", "DR"], ascending=False).head(8)["Squadra"].tolist()
    else: migliori_terze = []
        
    top_32 = []
    for g in rankings_finali: top_32.extend(rankings_finali[g][:2])
    top_32.extend(migliori_terze)
    return top_32

@st.cache_data(ttl=600)
def get_admin_dashboard_data():
    try:
        gc = get_gspread_client()
        sh = gc.open_by_key(ID_DEL_FOGLIO)
        try: ws_pro = sh.worksheet("Pronostici")
        except: return pd.DataFrame(), [], None, []
        try: ws_real = sh.worksheet("RisultatiReali")
        except: ws_real = None
            
        dati_utenti = ws_pro.get_all_values()
        if not dati_utenti: return pd.DataFrame(), [], ws_pro, []
            
        reali_dict = {}; reali_bracket = {}; reali_top_scorer = ""
        if ws_real:
            dati_reali = ws_real.get_all_values()
            for row in reversed(dati_reali):
                if len(row) >= 2:
                    data = safe_json_parse(row[1])
                    if isinstance(data, dict):
                        reali_top_scorer = data.get("TopScorer", "")
                        reali_dict = data.get("Gironi", data)
                        reali_bracket = data.get("Bracket", {})
                        break

        adm_32 = get_32_qualifiers(reali_dict) if reali_dict else []
        adm_16 = [reali_bracket.get(k) for k in BRACKET_KEYS if k.startswith("S") and reali_bracket.get(k) not in ["TBD", None]]
        adm_8  = [reali_bracket.get(k) for k in BRACKET_KEYS if k.startswith("O") and reali_bracket.get(k) not in ["TBD", None]]
        adm_4  = [reali_bracket.get(k) for k in BRACKET_KEYS if k.startswith("Q") and reali_bracket.get(k) not in ["TBD", None]]
        adm_2  = [reali_bracket.get(k) for k in BRACKET_KEYS if k.startswith("SEM") and reali_bracket.get(k) not in ["TBD", None]]
        adm_win = reali_bracket.get("WINNER") if reali_bracket.get("WINNER") != "TBD" else ""
        adm_fin = [t for t in adm_2 if t != adm_win]
        adm_fin = adm_fin[0] if adm_fin else ""
        adm_third = reali_bracket.get("THIRD") if reali_bracket.get("THIRD") != "TBD" else ""

        classifica = []; nomi_utenti = []; dettagli_list = []
        for idx, row in enumerate(dati_utenti):
            if len(row) < 2: continue
            nick = row[0]
            user_data = safe_json_parse(row[1])
            if not isinstance(user_data, dict): continue
            nomi_utenti.append((nick, idx + 1))
            
            user_gironi = user_data.get("Gironi", user_data); user_bracket = user_data.get("Bracket", {}); user_top_scorer = user_data.get("TopScorer", "")
            punti_tot = 0; punti_bonus = 0; dettaglio_utente = {"Partecipante": nick}
            
            for i, m in enumerate(MATCHES):
                key_str = f"G_{m['gr']} {m['h']}-{m['a']}"; key_num = str(i); pt_match = 0; is_esatto = False
                r_vals = reali_dict.get(key_str, reali_dict.get(key_num))
                if isinstance(r_vals, list) and len(r_vals) >= 2:
                    r_h = force_int(r_vals[0]); r_a = force_int(r_vals[1])
                    if r_h is not None and r_a is not None:
                        u_vals = user_gironi.get(key_str, user_gironi.get(key_num))
                        u_h, u_a = 0, 0
                        if isinstance(u_vals, list) and len(u_vals) >= 2:
                            if force_int(u_vals[0]) is not None: u_h = force_int(u_vals[0])
                            if force_int(u_vals[1]) is not None: u_a = force_int(u_vals[1])
                        u_esito = 1 if u_h > u_a else (2 if u_a > u_h else 0)
                        r_esito = 1 if r_h > r_a else (2 if r_a > r_h else 0)
                        p1 = RANKING.get(m['h'], 0); p2 = RANKING.get(m['a'], 0); px = (p1 + p2) // 2
                        
                        if u_esito == r_esito:
                            if r_esito == 1: pt_match += p1
                            elif r_esito == 2: pt_match += p2
                            else: pt_match += px
                            if u_h == r_h and u_a == r_a: 
                                pt_match += 50; punti_bonus += 50; is_esatto = True
                                
                punti_tot += pt_match; dettaglio_utente[key_str] = f"{pt_match} (Esatto)" if is_esatto else pt_match
                
            usr_32 = get_32_qualifiers(user_gironi) if user_gironi else []
            usr_16 = [user_bracket.get(k) for k in BRACKET_KEYS if k.startswith("S") and user_bracket.get(k) not in ["TBD", None]]
            usr_8  = [user_bracket.get(k) for k in BRACKET_KEYS if k.startswith("O") and user_bracket.get(k) not in ["TBD", None]]
            usr_4  = [user_bracket.get(k) for k in BRACKET_KEYS if k.startswith("Q") and user_bracket.get(k) not in ["TBD", None]]
            usr_2  = [user_bracket.get(k) for k in BRACKET_KEYS if k.startswith("SEM") and user_bracket.get(k) not in ["TBD", None]]
            usr_win = user_bracket.get("WINNER") if user_bracket.get("WINNER") != "TBD" else ""
            usr_fin = [t
