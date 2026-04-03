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
st.set_page_config(page_title="FIFA World Cup Contest 2026", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800;900&display=swap');
    
    .stApp { background-color: #000000; color: #f8fafc; font-family: 'Inter', sans-serif; }
    
    .hero-header { text-align: center; padding: 1rem 0 1rem 0; }
    .hero-title {
        font-size: 3.5rem; font-weight: 900; margin-bottom: 0;
        background: linear-gradient(90deg, #00ff87, #60efff, #3b82f6);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }
    .hero-subtitle { color: #cbd5e1; font-size: 1.2rem; font-weight: 600; letter-spacing: 1px; }

    button[data-baseweb="tab"] p { font-size: 16px !important; font-weight: 700 !important; color: #94a3b8 !important; }
    button[data-baseweb="tab"][aria-selected="true"] p { color: #00ff87 !important; }

    .stElementContainer div[data-testid="stVerticalBlockBorderControl"] {
        background-color: #1a1a1a !important; border: 1px solid #444444 !important; 
        border-radius: 12px !important; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.5) !important;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .stElementContainer div[data-testid="stVerticalBlockBorderControl"]:hover {
        border-color: #60efff !important; box-shadow: 0 0 15px rgba(96, 239, 255, 0.4) !important;
    }
    
    input[type="number"], input[type="text"] {
        background-color: #2a2a2a !important; color: #ffffff !important;
        font-size: 20px !important; font-weight: 800 !important; border: 1px solid #444444 !important;
        border-radius: 8px !important; text-align: center !important; height: 45px !important;
    }
    input[type="number"]:focus, input[type="text"]:focus {
        border-color: #00ff87 !important; box-shadow: 0 0 0 3px rgba(0, 255, 135, 0.2) !important;
    }
    input[type="password"] { font-size: 14px !important; height: 35px !important; }
    
    .pts-badge { background: #2a2a2a; color: #60efff; padding: 4px 8px; border-radius: 6px; font-size: 11px; font-weight: 800; border: 1px solid #444444; margin: 0 3px; }
    .bonus-txt { color: #00ff87; font-size: 11px; font-weight: 800; display: block; text-align: center; margin-top: 8px; margin-bottom: 8px; }
    
    .admin-match-box { background: #1a1a1a; border: 1px solid #444444; border-radius: 8px; padding: 10px; margin-bottom: 12px; color: white;}
    .admin-match-title { font-size: 13px; font-weight: 800; text-align: center; color: #e2e8f0; margin-bottom: 8px; }
    
    div.stButton > button {
        border-radius: 8px; font-weight: 700; border: 1px solid #444444;
        background-color: #2a2a2a; color: #ffffff; margin-bottom: 0px !important;
    }
    div.stButton > button:hover { border-color: #60efff; color: #ffffff; background-color: #3a3a3a; }
    div.stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #00ff87 0%, #3b82f6 100%) !important;
        border: none !important; color: #000 !important; font-weight: 800 !important;
        box-shadow: 0 4px 10px rgba(0, 255, 135, 0.3) !important;
    }
    .bracket-round-title {
        font-size: 12px; font-weight: 900; text-transform: uppercase; letter-spacing: 1.5px;
        color: #000; background: #00ff87; padding: 6px 12px; border-radius: 20px;
        text-align: center; display: inline-block; border: 1px solid #00ff87; margin-bottom: 10px;
    }

    div[data-testid="stHorizontalBlock"]:has(.bracket-round-title) { align-items: stretch !important; }
    div[data-testid="column"]:has(.bracket-round-title) { display: flex !important; flex-direction: column !important; justify-content: space-around !important; }
    
    @media (max-width: 768px) {
        .hero-title { font-size: 2.2rem !important; }
        .hero-subtitle { font-size: 1rem !important; }
        div[data-testid="stVerticalBlockBorderControl"] { padding: 10px !important; }
        input[type="number"], input[type="text"] { font-size: 16px !important; height: 38px !important; }
        div.stButton > button { font-size: 12px !important; padding: 2px 5px !important; min-height: 35px !important; }
    }
</style>
""", unsafe_allow_html=True)

# --- LOGIN ADMIN CORTISSIMO ED ALLINEATO A DESTRA ---
col_spacer, col_admin = st.columns([11, 1])
with col_admin:
    admin_pw = st.text_input("Admin Login", type="password", key="admin_auth", label_visibility="collapsed", placeholder="🔒")
is_admin = (admin_pw == "mondiali2026")

# --- 2. INIZIALIZZAZIONE MEMORIA (ANTI-CRASH) ---
if "initialized" not in st.session_state:
    for i in range(72):
        st.session_state[f"h_{i}"] = 0; st.session_state[f"a_{i}"] = 0
        st.session_state[f"adm_h_{i}"] = None; st.session_state[f"adm_a_{i}"] = None  
    for k in [f"S{i}" for i in range(1,17)] + [f"O{i}" for i in range(1,9)] + [f"Q{i}" for i in range(1,5)] + ["SEM1", "SEM2", "WINNER"]:
        st.session_state[k] = "TBD"; st.session_state[f"adm_{k}"] = "TBD"
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
    for h, a in [(0, 1), (2, 3), (0, 2), (1, 3), (0, 3), (1, 2)]: MATCHES.append({"gr": gid, "h": teams[h], "a": teams[a]})
BRACKET_KEYS = [f"S{i}" for i in range(1,17)] + [f"O{i}" for i in range(1,9)] + [f"Q{i}" for i in range(1,5)] + ["SEM1", "SEM2", "WINNER"]

def get_flag(t):
    if not t or t in ["TBD", "In attesa..."]: return "https://flagcdn.com/w160/un.png"
    m = {"Messico": "mx", "Sudafrica": "za", "Sudcorea": "kr", "Repubblica Ceca": "cz", "Canada": "ca", "Bosnia Erzegovina": "ba", "Qatar": "qa", "Svizzera": "ch", "Brasile": "br", "Marocco": "ma", "Haiti": "ht", "Scozia": "gb-sct", "USA": "us", "Paraguay": "py", "Australia": "au", "Turchia": "tr", "Germania": "de", "Curacao": "cw", "Costa D'Avorio": "ci", "Ecuador": "ec", "Olanda": "nl", "Giappone": "jp", "Svezia": "se", "Tunisia": "tn", "Belgio": "be", "Egitto": "eg", "Iran": "ir", "Nuova Zelanda": "nz", "Spagna": "es", "Capo Verde": "cv", "Arabia Saudita": "sa", "Uruguay": "uy", "Francia": "fr", "Senegal": "sn", "Iraq": "iq", "Norvegia": "no", "Argentina": "ar", "Algeria": "dz", "Austria": "at", "Giordania": "jo", "Portogallo": "pt", "DR Congo": "cd", "Uzbekistan": "uz", "Colombia": "co", "Inghilterra": "gb-eng", "Croazia": "hr", "Ghana": "gh", "Panama": "pa", "Italia": "it"}
    return f"https://flagcdn.com/w160/{m.get(t, 'un')}.png"

# --- 4. CONNESSIONE E LOGICA ---
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
            except Exception as e2:
                try: ws.update([dati_matrice])
                except Exception as e3: return f"API Gspread bloccata."
        return "OK"
    except Exception as e: return f"Errore: {str(e)}"

def safe_json_parse(val):
    try: return json.loads(val)
    except: return {}

def force_int(val):
    try:
        if val is None: return None
        s = str(val).strip().lower()
        if s == "" or s == "none" or s == "null": return None
        return int(float(s))
    except: return None

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
                    for i, m in enumerate(MATCHES):
                        key_str = f"G_{m['gr']} {m['h']}-{m['a']}"
                        if key_str in gironi_data:
                            st.session_state[f"adm_h_{i}"] = force_int(gironi_data[key_str][0])
                            st.session_state[f"adm_a_{i}"] = force_int(gironi_data[key_str][1])
                    for k, v in bracket_data.items():
                        st.session_state[f"adm_{k}"] = v
                    break
    except Exception: pass

def get_32_qualifiers(gironi_dict):
    stats = {g: {t: {"Pt": 0, "DR": 0, "GF": 0} for t in ts} for g, ts in G_TEAMS.items()}
    for i, m in enumerate(MATCHES):
        key_str = f"G_{m['gr']} {m['h']}-{m['a']}"
        key_num = str(i)
        vals = gironi_dict.get(key_str, gironi_dict.get(key_num))
        if isinstance(vals, list) and len(vals) >= 2:
            h = force_int(vals[0]); a = force_int(vals[1])
            if h is not None and a is not None:
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
        terze_squadre.append({"Squadra": df.index[2], "Pt": df.iloc[2]["Pt"], "DR": df.iloc[2]["DR"]})
    migliori_terze = pd.DataFrame(terze_squadre).sort_values(["Pt", "DR"], ascending=False).head(8)["Squadra"].tolist()
    
    top_32 = []
    for g in rankings_finali: top_32.extend(rankings_finali[g][:2])
    top_32.extend(migliori_terze)
    return top_32

# --- CALCOLO CLASSIFICA CON LOGICA PUNTI ESATTA ---
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
        
        reali_dict = {}; reali_bracket = {}
        if ws_real:
            dati_reali = ws_real.get_all_values()
            for row in reversed(dati_reali):
                if len(row) >= 2:
                    data = safe_json_parse(row[1])
                    if isinstance(data, dict):
                        if "Gironi" in data: 
                            reali_dict = data["Gironi"]
                            if "Bracket" in data: reali_bracket = data["Bracket"]
                        elif any(k.startswith("G_") or str(k).isdigit() for k in data.keys()): 
                            reali_dict = data
                        break

        # SQUADRE QUALIFICATE REALI
        adm_32 = get_32_qualifiers(reali_dict) if reali_dict else []
        adm_16 = [reali_bracket.get(k) for k in BRACKET_KEYS if k.startswith("S") and reali_bracket.get(k) not in ["TBD", "In attesa...", None]]
        adm_8  = [reali_bracket.get(k) for k in BRACKET_KEYS if k.startswith("O") and reali_bracket.get(k) not in ["TBD", "In attesa...", None]]
        adm_4  = [reali_bracket.get(k) for k in BRACKET_KEYS if k.startswith("Q") and reali_bracket.get(k) not in ["TBD", "In attesa...", None]]
        adm_2  = [reali_bracket.get(k) for k in BRACKET_KEYS if k.startswith("SEM") and reali_bracket.get(k) not in ["TBD", "In attesa...", None]]
        adm_win = reali_bracket.get("WINNER") if reali_bracket.get("WINNER") not in ["TBD", "In attesa...", None] else ""
        adm_fin = [t for t in adm_2 if t != adm_win]
        adm_fin = adm_fin[0] if adm_fin else ""

        classifica = []
        nomi_utenti = []
        dettagli_list = [] 
        
        for idx, row in enumerate(dati_utenti):
            if len(row) < 2: continue
            
            nick = row[0]
            user_data = safe_json_parse(row[1])
            if not isinstance(user_data, dict): continue
            
            nomi_utenti.append((nick, idx + 1))
            user_gironi = user_data.get("Gironi", user_data)
            user_bracket = user_data.get("Bracket", {})
            if not isinstance(user_gironi, dict): continue
            
            punti_tot = 0; punti_bonus = 0
            dettaglio_utente = {"Partecipante": nick}
            
            # Punti dei Gironi
            for i, m in enumerate(MATCHES):
                key_str = f"G_{m['gr']} {m['h']}-{m['a']}"
                key_num = str(i)
                pt_match = 0
                
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
                            pt_match += 50
                            punti_bonus += 50
                            
                punti_tot += pt_match
                dettaglio_utente[key_str] = pt_match
            
            # Punti del Bracket
            usr_32 = get_32_qualifiers(user_gironi) if user_gironi else []
            usr_16 = [user_bracket.get(k) for k in BRACKET_KEYS if k.startswith("S") and user_bracket.get(k) not in ["TBD", "In attesa...", None]]
            usr_8  = [user_bracket.get(k) for k in BRACKET_KEYS if k.startswith("O") and user_bracket.get(k) not in ["TBD", "In attesa...", None]]
            usr_4  = [user_bracket.get(k) for k in BRACKET_KEYS if k.startswith("Q") and user_bracket.get(k) not in ["TBD", "In attesa...", None]]
            usr_2  = [user_bracket.get(k) for k in BRACKET_KEYS if k.startswith("SEM") and user_bracket.get(k) not in ["TBD", "In attesa...", None]]
            usr_win = user_bracket.get("WINNER") if user_bracket.get("WINNER") not in ["TBD", "In attesa...", None] else ""
            usr_fin = [t for t in usr_2 if t != usr_win]
            usr_fin = usr_fin[0] if usr_fin else ""

            # INTERSEZIONE INSIEMI PER ASSEGNAZIONE ESATTA PUNTI
            pt_32 = len(set(usr_32) & set(adm_32)) * 25
            pt_16 = len(set(usr_16) & set(adm_16)) * 35
            pt_8 = len(set(usr_8) & set(adm_8)) * 50
            pt_4 = len(set(usr_4) & set(adm_4)) * 80
            pt_2 = len(set(usr_2) & set(adm_2)) * 120
            pt_finalista = 180 if usr_fin and adm_fin and usr_fin == adm_fin else 0
            pt_vincitore = 250 if usr_win and adm_win and usr_win == adm_win else 0

            punti_tot += pt_32 + pt_16 + pt_8 + pt_4 + pt_2 + pt_finalista + pt_vincitore
            
            dettaglio_utente["PT_Sedicesimi_(32)"] = pt_32
            dettaglio_utente["PT_Ottavi_(16)"] = pt_16
            dettaglio_utente["PT_Quarti_(8)"] = pt_8
            dettaglio_utente["PT_Semi_(4)"] = pt_4
            dettaglio_utente["PT_Finali_(2)"] = pt_2
            dettaglio_utente["PT_Finalista_Perdente"] = pt_finalista
            dettaglio_utente["PT_Vincitore"] = pt_vincitore
            
            dettaglio_utente["Punti Totali"] = punti_tot
            dettaglio_utente["Punti Bonus"] = punti_bonus
            dettagli_list.append(dettaglio_utente)
            
            classifica.append({"Partecipante": nick, "Punti Totali": punti_tot, "Bonus Esatti": punti_bonus})
            
        df = pd.DataFrame(classifica)
        if not df.empty:
            df = df.groupby('Partecipante', as_index=False).last()
            df = df.sort_values(by=["Punti Totali", "Bonus Esatti"], ascending=[False, False]).reset_index(drop=True)
            df.index += 1
        return df, nomi_utenti, ws_pro, dettagli_list
    except Exception as e: return pd.DataFrame(), [], None, []

def elimina_utente(ws, row_index):
    try: ws.delete_row(int(row_index))
    except:
        try: ws.delete_rows(int(row_index)); return True
        except: return False
    return True

# --- 5. CALCOLI CLASSIFICHE GIRONI E TERZE SQUADRE ---
def calcola_classifiche(prefisso=""):
    stats = {g: {t: {"Pt": 0, "DR": 0, "GF": 0} for t in ts} for g, ts in G_TEAMS.items()}
    for i, m in enumerate(MATCHES):
        h = st.session_state[f"{prefisso}h_{i}"]
        a = st.session_state[f"{prefisso}a_{i}"]
        if h is None or a is None or str(h).strip() == "" or str(a).strip() == "": continue
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
        terze_squadre.append({"Squadra": df.index[2], "Girone": g, "Pt": df.iloc[2]["Pt"], "DR": df.iloc[2]["DR"], "GF": df.iloc[2]["GF"]})
    
    # Crea la tabella di tutte le terze e le ordina
    terze_squadre_df = pd.DataFrame(terze_squadre).sort_values(["Pt", "DR", "GF"], ascending=False).reset_index(drop=True)
    terze_squadre_df.index += 1
    
    migliori_terze = terze_squadre_df.head(8)["Squadra"].tolist()
    return rankings_finali, migliori_terze, stats, terze_squadre_df

# --- CREAZIONE PDF ---
def genera_pdf_b64(user, gironi_data, bracket_data):
    if not HAS_FPDF: return None
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt=f"Pronostici Ufficiali - WC 2026 Contest", ln=True, align='C')
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, txt=f"Partecipante: {user}", ln=True, align='C')
    pdf.ln(10)
    
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, txt="FASE A GIRONI", ln=True, align='L')
    pdf.set_font("Arial", size=10)
    
    for i, m in enumerate(MATCHES):
        key = f"G_{m['gr']} {m['h']}-{m['a']}"
        h_score, a_score = gironi_data.get(key, ["-", "-"])
        pdf.cell(200, 6, txt=f"Girone {m['gr']}: {m['h']} {h_score} - {a_score} {m['a']}", ln=True)
        
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, txt="FASE A ELIMINAZIONE DIRETTA", ln=True, align='L')
    pdf.set_font("Arial", size=10)
    
    for k in BRACKET_KEYS:
        val = bracket_data.get(k, "TBD")
        pdf.cell(200, 6, txt=f"Vincitore {k}: {val}", ln=True)
        
    pdf_bytes = pdf.output(dest='S').encode('latin1')
    return base64.b64encode(pdf_bytes).decode()


# --- 6. INTERFACCIA MAIN ---

if is_admin and not st.session_state.get("paracadute_attivato"):
    carica_dati_paracadute()
    st.session_state["paracadute_attivato"] = True

# Logo in homepage centrato
col_img1, col_img2, col_img3 = st.columns([2, 1, 2])
with col_img2:
    st.image("logo.png", use_container_width=True)

st.markdown("""
<div class='hero-header'>
    <h1 class='hero-title'>FIFA World Cup Contest 2026</h1>
    <p class='hero-subtitle'>Pronostica. Sfida. Domina.</p>
</div>
""", unsafe_allow_html=True)

user = ""

if not is_admin:
    st.write("<br>", unsafe_allow_html=True)
    c_space1, c_nick, c_space2 = st.columns([1, 1.5, 1])
    with c_nick:
        st.markdown("<h4 style='text-align:center; color:#e2e8f0; margin-bottom: 15px;'>Inserisci il tuo Nickname per iniziare</h4>", unsafe_allow_html=True)
        user = st.text_input("Nickname:", placeholder="Es. Marco_88", label_visibility="collapsed")

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
                    st.session_state[f"h_{i}"] = random.randint(0, 4); st.session_state[f"a_{i}"] = random.randint(0, 4)
                st.rerun()

        st.write("<br>", unsafe_allow_html=True)

        for r in range(18):
            cols = st.columns(4)
            for c in range(4):
                idx = r * 4 + c
                if idx < 72:
                    m = MATCHES[idx]; p1, p2 = RANKING[m['h']], RANKING[m['a']]; px = (p1 + p2) // 2
                    with cols[c]:
                        with st.container(border=True):
                            st.markdown(f"<div style='text-align:center;'><span class='pts-badge'>1: {p1}pt</span><span class='pts-badge'>X: {px}pt</span><span class='pts-badge'>2: {p2}pt</span></div>", unsafe_allow_html=True)
                            st.markdown("<span class='bonus-txt'>🎯 +50 pt Risultato Esatto</span><br>", unsafe_allow_html=True)
                            
                            c1, in1, vs, in2, c2 = st.columns([1.3, 1.1, 0.2, 1.1, 1.3])
                            c1.markdown(f"<div style='text-align:center; margin-top: 2px;'><img src='{get_flag(m['h'])}' width='48' style='border-radius:4px; box-shadow: 0 2px 4px rgba(0,0,0,0.4);'><br><span style='font-size:10.5px; font-weight:800; color:#e2e8f0; display:block; margin-top:4px; line-height:1.1;'>{m['h']}</span></div>", unsafe_allow_html=True)
                            in1.number_input("H", min_value=0, max_value=9, key=f"h_{idx}", label_visibility="collapsed")
                            vs.markdown("<p style='text-align:center; padding-top:6px; font-weight:900; color:#cbd5e1;'>-</p>", unsafe_allow_html=True)
                            in2.number_input("A", min_value=0, max_value=9, key=f"a_{idx}", label_visibility="collapsed")
                            c2.markdown(f"<div style='text-align:center; margin-top: 2px;'><img src='{get_flag(m['a'])}' width='48' style='border-radius:4px; box-shadow: 0 2px 4px rgba(0,0,0,0.4);'><br><span style='font-size:10.5px; font-weight:800; color:#e2e8f0; display:block; margin-top:4px; line-height:1.1;'>{m['a']}</span></div>", unsafe_allow_html=True)

    # --- TAB CLASSIFICHE ---
    with tabs[1]:
        r_usr, t3_usr, stats_usr, df_terze = calcola_classifiche(prefisso="")
        for i in range(0, 12, 3):
            cs = st.columns(3)
            for k in range(3):
                gid = list(G_TEAMS.keys())[i+k]
                df = pd.DataFrame(stats_usr[gid]).T.sort_values(["Pt", "DR", "GF"], ascending=False)
                cs[k].markdown(f"<h4 style='color:#60efff;'>Gruppo {gid}</h4>", unsafe_allow_html=True)
                cs[k].dataframe(df, use_container_width=True)
                
        st.divider()
        st.markdown("<h3 style='text-align:center; color:#00ff87;'>Classifica 3° Classificate</h3>", unsafe_allow_html=True)
        st.markdown("<p style='text-align:center; color:#cbd5e1;'>Solo le prime 8 accedono alla fase ad eliminazione diretta.</p>", unsafe_allow_html=True)
        col_t1, col_t2, col_t3 = st.columns([1, 2, 1])
        with col_t2:
            st.dataframe(df_terze.style.apply(lambda x: ['background-color: #064e3b; color: #ffffff;' if x.name <= 8 else '' for i in x], axis=1), use_container_width=True)

    # --- TAB BRACKET: STRUTTURA AD ALBERO MATEMATICA E COMPATTA ---
    def render_wimbledon(prefisso=""):
        ranks, terze_list, _, _ = calcola_classifiche(prefisso)
        def s_t(g, pos):
            try: return ranks[g][pos]
            except: return "TBD"
        def s_t3(index):
            try: return terze_list[index]
            except: return "TBD"
        def t_box(t1, t2, mid):
            with st.container(border=True):
                st.markdown(f"<div style='font-size:10px; color:#60efff; font-weight:800; text-align:center; margin-bottom:2px;'>MATCH {mid}</div>", unsafe_allow_html=True)
                if st.button(t1, key=f"btn1_{prefisso}{mid}", use_container_width=True, type="primary" if st.session_state[prefisso+mid]==t1 else "secondary"):
                    st.session_state[prefisso+mid]=t1; st.rerun()
                if st.button(t2, key=f"btn2_{prefisso}{mid}", use_container_width=True, type="primary" if st.session_state[prefisso+mid]==t2 else "secondary"):
                    st.session_state[prefisso+mid]=t2; st.rerun()
            return st.session_state[prefisso+mid]

        st.info("🎾 **Bracket Mode:** Clicca sul nome della squadra vincitrice in ogni riquadro per farla avanzare.")
        c_sed, c_ott, c_qua, c_sem, c_fin = st.columns(5)

        with c_sed:
            st.markdown("<div style='text-align:center; height:30px;'><span class='bracket-round-title'>Sedicesimi</span></div>", unsafe_allow_html=True)
            s1 = t_box(s_t("A",0), s_t3(0), "S1"); s2 = t_box(s_t("B",1), s_t("C",1), "S2")
            s3 = t_box(s_t("D",0), s_t3(1), "S3"); s4 = t_box(s_t("E",1), s_t("F",1), "S4")
            s5 = t_box(s_t("G",0), s_t3(2), "S5"); s6 = t_box(s_t("H",1), s_t("I",1), "S6")
            s7 = t_box(s_t("J",0), s_t3(3), "S7"); s8 = t_box(s_t("K",1), s_t("L",1), "S8")
            s9 = t_box(s_t("B",0), s_t3(4), "S9"); s10= t_box(s_t("E",0), s_t("A",1), "S10")
            s11= t_box(s_t("C",0), s_t3(5), "S11"); s12= t_box(s_t("F",0), s_t("D",1), "S12")
            s13= t_box(s_t("H",0), s_t3(6), "S13"); s14= t_box(s_t("K",0), s_t("G",1), "S14")
            s15= t_box(s_t("I",0), s_t3(7), "S15"); s16= t_box(s_t("L",0), s_t("J",1), "S16")
            
        with c_ott:
            st.markdown("<div style='text-align:center; height:30px;'><span class='bracket-round-title'>Ottavi</span></div>", unsafe_allow_html=True)
            o1 = t_box(s1, s2, "O1"); o2 = t_box(s3, s4, "O2")
            o3 = t_box(s5, s6, "O3"); o4 = t_box(s7, s8, "O4")
            o5 = t_box(s9, s10, "O5"); o6 = t_box(s11, s12, "O6")
            o7 = t_box(s13, s14, "O7"); o8 = t_box(s15, s16, "O8")

        with c_qua:
            st.markdown("<div style='text-align:center; height:30px;'><span class='bracket-round-title'>Quarti</span></div>", unsafe_allow_html=True)
            q1 = t_box(o1, o2, "Q1"); q2 = t_box(o3, o4, "Q2")
            q3 = t_box(o5, o6, "Q3"); q4 = t_box(o7, o8, "Q4")

        with c_sem:
            st.markdown("<div style='text-align:center; height:30px;'><span class='bracket-round-title'>Semi</span></div>", unsafe_allow_html=True)
            sem1 = t_box(q1, q2, "SEM1"); sem2 = t_box(q3, q4, "SEM2")

        with c_fin:
            st.markdown("<div style='text-align:center; height:30px;'><span class='bracket-round-title' style='background: linear-gradient(90deg, #00ff87, #60efff); color:#000;'>🏆 FINALE</span></div>", unsafe_allow_html=True)
            vinc_key = "adm_vincitore" if prefisso == "adm_" else "WINNER"; win = t_box(sem1, sem2, "WINNER")
            st.session_state[vinc_key] = win

    with tabs[2]:
        render_wimbledon(prefisso="")

    # --- INVIO UTENTE E PDF ---
    if user:
        with tabs[3]:
            st.write("### 🚀 Manda i Pronostici Ufficiali")
            if st.session_state.get("user_saved_success"): st.success(f"✅ Ottimo lavoro {user}, i tuoi pronostici sono stati salvati!"); st.session_state["user_saved_success"] = False
            
            c_snd, c_pdf = st.columns(2)
            with c_snd:
                if st.button("INVIA I TUOI PRONOSTICI DEFINITIVAMENTE", type="primary", use_container_width=True):
                    payload_user = {f"G_{MATCHES[i]['gr']} {MATCHES[i]['h']}-{MATCHES[i]['a']}": [st.session_state[f"h_{i}"], st.session_state[f"a_{i}"]] for i in range(72)}
                    payload_bracket = {k: st.session_state[k] for k in BRACKET_KEYS}
                    if invia_google_sheets("Pronostici", user, {"Gironi": payload_user, "Bracket": payload_bracket}):
                        st.session_state["user_saved_success"] = True; time.sleep(1); st.rerun()
            
            with c_pdf:
                if HAS_FPDF:
                    payload_user_tmp = {f"G_{MATCHES[i]['gr']} {MATCHES[i]['h']}-{MATCHES[i]['a']}": [st.session_state[f"h_{i}"], st.session_state[f"a_{i}"]] for i in range(72)}
                    payload_bracket_tmp = {k: st.session_state[k] for k in BRACKET_KEYS}
                    pdf_b64 = genera_pdf_b64(user, payload_user_tmp, payload_bracket_tmp)
                    if pdf_b64:
                        href = f'<a href="data:application/pdf;base64,{pdf_b64}" download="Pronostici_WC2026_{user}.pdf" style="text-decoration: none;"><div style="background-color: #2a2a2a; border: 1px solid #444444; color: #ffffff; padding: 10px; text-align: center; border-radius: 8px; font-weight: bold; cursor: pointer;">📄 Scarica le tue scelte in PDF</div></a>'
                        st.markdown(href, unsafe_allow_html=True)
                else:
                    st.info("⚠️ Crea un file 'requirements.txt' con la scritta 'fpdf' per abilitare il download PDF.")

    # --- ADMIN AREA ---
    if is_admin:
        with tabs[-1]:
            st.header("👑 Pannello Admin")
            if st.session_state.get("admin_saved_success"): st.success("✅ Risultati e Tabellone salvati con successo!")
            if st.session_state.get("admin_dettagli_errore"): st.error(f"❌ Errore Dettaglio Punti: {st.session_state['admin_dettagli_errore']}"); st.session_state["admin_dettagli_errore"] = None

            adm_tabs = st.tabs(["📊 Ranking Partecipanti", "⚽ Inserimento Risultati Reali", "🏆 Bracket Reale", "🗑️ Reset Dati"])
            
            with adm_tabs[0]:
                st.write("### Classifica Ufficiale")
                df_ranking, nomi_utenti, ws_pronostici, _ = get_admin_dashboard_data()
                if not df_ranking.empty:
                    st.dataframe(df_ranking, use_container_width=True)
                    
                    testo_wa = "🏆 *Classifica WC 2026 Contest* 🏆%0A%0A"
                    for idx, r_data in df_ranking.iterrows():
                        testo_wa += f"{idx}. {r_data['Partecipante']} - {r_data['Punti Totali']} pt%0A"
                    st.markdown(f'''
                    <a href="https://wa.me/?text={testo_wa}" target="_blank" style="text-decoration:none;">
                        <div style="background-color: #25D366; color: white; padding: 10px; text-align: center; border-radius: 8px; font-weight: bold; margin-bottom: 15px; margin-top: 5px;">
                            💬 Condividi Classifica su WhatsApp
                        </div>
                    </a>
                    ''', unsafe_allow_html=True)
                    
                    st.write("#### Gestione Utenti")
                    col_del1, col_del2 = st.columns([2, 1])
                    with col_del1: utente_da_eliminare = st.selectbox("Seleziona Partecipante", options=nomi_utenti, format_func=lambda x: f"{x[0]} (Riga: {x[1]})")
                    with col_del2:
                        st.write("<br>", unsafe_allow_html=True)
                        if st.button("🗑️ Elimina Utente", type="primary"):
                            if utente_da_eliminare and elimina_utente(ws_pronostici, utente_da_eliminare[1]):
                                get_admin_dashboard_data.clear(); st.rerun()
                else: st.warning("Nessun dato calcolabile.")

            with adm_tabs[1]:
                if st.button("🪄 Autocompila Reali (Test)"):
                    for i in range(72): st.session_state[f"adm_h_{i}"] = random.randint(0, 3); st.session_state[f"adm_a_{i}"] = random.randint(0, 3)
                    st.rerun()
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
                        
            with adm_tabs[2]: render_wimbledon(prefisso="adm_")
            
            with adm_tabs[3]:
                st.write("### 🗑️ RESET TOTALE")
                st.error("QUESTA AZIONE È IRREVERSIBILE! Cancellerà tutti i risultati reali inseriti (Gironi e Bracket) su Google Sheets.")
                st.warning("Dopo il reset, l'app si ricaricherà e tutti i campi di inserimento per l'admin appariranno vuoti o con 'TBD'.")
                if st.button("CANCELLA DEFINITIVAMENTE TUTTI I DATI REALI", type="primary", use_container_width=True):
                    if invia_google_sheets("RisultatiReali", "ADMIN", {"Gironi": {}, "Bracket": {}}):
                        get_admin_dashboard_data.clear()
                        st.success("✅ Dati reali cancellati su Google Sheets. Ricaricamento dell'app per azzerare la memoria locale...")
                        time.sleep(1.5)
                        st.rerun()
                
            st.divider()
            if st.button("💾 SALVA TUTTO E AGGIORNA CLASSIFICA", type="primary", use_container_width=True):
                payload_adm = {f"G_{MATCHES[i]['gr']} {MATCHES[i]['h']}-{MATCHES[i]['a']}": [st.session_state.get(f"adm_h_{i}"), st.session_state.get(f"adm_a_{i}")] for i in range(72)}
                payload_adm_bracket = {k.replace("adm_", ""): st.session_state[k] for k in [f"adm_{k}" for k in BRACKET_KEYS]}
                
                if invia_google_sheets("RisultatiReali", "ADMIN", {"Gironi": payload_adm, "Bracket": payload_adm_bracket}):
                    get_admin_dashboard_data.clear() 
                    _, _, _, dettagli_list_gs = get_admin_dashboard_data()
                    esito_dettagli = salva_dettaglio_punti_sheets(dettagli_list_gs)
                    st.session_state["admin_saved_success"] = True
                    if esito_dettagli != "OK": st.session_state["admin_dettagli_errore"] = esito_dettagli
                    time.sleep(1) 
                    st.rerun()
