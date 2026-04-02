import streamlit as st
import pandas as pd
import json
import gspread
import random
from google.oauth2.service_account import Credentials

# --- 1. CONFIGURAZIONE PAGINA E GRAFICA ---
st.set_page_config(page_title="WC 2026 Prediction Contest", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    
    .stApp { background-color: #f8fafc; color: #1e293b; font-family: 'Inter', sans-serif; }
    
    /* Login Admin in alto a DX */
    .admin-zone { position: absolute; top: 0; right: 0; padding: 10px; z-index: 100; }
    
    /* TAB */
    button[data-baseweb="tab"] { height: 60px !important; }
    button[data-baseweb="tab"] p { font-size: 18px !important; font-weight: 700 !important; color: #64748b !important; }
    button[data-baseweb="tab"][aria-selected="true"] p { color: #0284c7 !important; }

    /* CARD PARTITE CHIARA E PULITA */
    .stElementContainer div[data-testid="stVerticalBlockBorderControl"] {
        background-color: #ffffff !important; border: 1px solid #cbd5e1 !important; 
        border-radius: 12px !important; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05) !important;
    }
    
    /* INPUT RISULTATI */
    input[type="number"] {
        background-color: #f1f5f9 !important; color: #0f172a !important;
        font-size: 24px !important; font-weight: 900 !important; border: 2px solid #cbd5e1 !important;
        border-radius: 8px !important; text-align: center !important; height: 45px !important;
    }
    
    /* STILE BADGE PUNTI */
    .pts-container { display: flex; justify-content: center; gap: 10px; margin-bottom: 8px; }
    .pts-badge { background: #f0f9ff; color: #0369a1; padding: 4px 8px; border-radius: 6px; font-size: 11px; font-weight: 800; border: 1px solid #bae6fd; }
    .bonus-badge { background: #fef2f2; color: #b91c1c; padding: 2px 6px; border-radius: 4px; font-size: 10px; font-weight: 800; text-align: center; display: block; margin-bottom: 10px;}
    
    .team-label { color: #1e293b; font-weight: 700; font-size: 13px; text-align: center; margin-top: 5px; }
</style>
""", unsafe_allow_html=True)

# --- 2. DATABASE RANKING (Estratto da PDF) ---
RANKING = {
    "Spagna": 1, "Argentina": 2, "Francia": 3, "Inghilterra": 4, "Brasile": 5, "Portogallo": 6, "Olanda": 7, "Belgio": 8,
    "Germania": 9, "Croazia": 10, "Marocco": 11, "Colombia": 13, "Italia": 13, "USA": 14, "Messico": 15, "Uruguay": 16,
    "Svizzera": 17, "Giappone": 18, "Senegal": 19, "Iran": 20, "Sudcorea": 22, "Ecuador": 23, "Austria": 24, "Turchia": 25,
    "Australia": 26, "Canada": 27, "Norvegia": 29, "Panama": 30, "Egitto": 34, "Algeria": 35, "Scozia": 36, "Paraguay": 39,
    "Tunisia": 40, "Costa D'Avorio": 42, "Svezia": 43, "Repubblica Ceca": 44, "Uzbekistan": 50, "DR Congo": 56, "Qatar": 58,
    "Iraq": 58, "Arabia Saudita": 60, "Sudafrica": 61, "Giordania": 66, "Capo Verde": 68, "Bosnia Erzegovina": 71, "Ghana": 72,
    "Curacao": 82, "Haiti": 84, "Nuova Zelanda": 86
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

def get_matches():
    g = get_groups()
    ml = []
    for gid, teams in g.items():
        for h, a in [(0, 1), (2, 3), (0, 2), (1, 3), (0, 3), (1, 2)]:
            ml.append({"gr": gid, "h": teams[h], "a": teams[a]})
    return ml

MATCHES = get_matches()

def get_flag(t):
    if not t or t in ["???", "TBD"]: return "https://flagcdn.com/w160/un.png"
    m = {"Messico": "mx", "Sudafrica": "za", "Sudcorea": "kr", "Repubblica Ceca": "cz", "Canada": "ca", "Bosnia Erzegovina": "ba", "Qatar": "qa", "Svizzera": "ch", "Brasile": "br", "Marocco": "ma", "Haiti": "ht", "Scozia": "gb-sct", "USA": "us", "Paraguay": "py", "Australia": "au", "Turchia": "tr", "Germania": "de", "Curacao": "cw", "Costa D'Avorio": "ci", "Ecuador": "ec", "Olanda": "nl", "Giappone": "jp", "Svezia": "se", "Tunisia": "tn", "Belgio": "be", "Egitto": "eg", "Iran": "ir", "Nuova Zelanda": "nz", "Spagna": "es", "Capo Verde": "cv", "Arabia Saudita": "sa", "Uruguay": "uy", "Francia": "fr", "Senegal": "sn", "Iraq": "iq", "Norvegia": "no", "Argentina": "ar", "Algeria": "dz", "Austria": "at", "Giordania": "jo", "Portogallo": "pt", "DR Congo": "cd", "Uzbekistan": "uz", "Colombia": "co", "Inghilterra": "gb-eng", "Croazia": "hr", "Ghana": "gh", "Panama": "pa", "Italia": "it"}
    return f"https://flagcdn.com/w160/{m.get(t, 'un')}.png"

# --- 3. GOOGLE SHEETS LOGIC ---
def send_to_google(tab, nick, payload):
    try:
        conf = json.loads(st.secrets["service_account"])
        creds = Credentials.from_service_account_info(conf, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
        gc = gspread.authorize(creds)
        URL = "https://docs.google.com/spreadsheets/d/1palUSBw4IlBFzU4dKtgT0tnjPiPEtxIc6K-DK05vXG8/edit?gid=0#gid=0" # INSERISCI IL LINK DEL TUO GOOGLE SHEET
        sh = gc.open_by_url(URL)
        ws = sh.worksheet(tab) if tab in [w.title for w in sh.worksheets()] else sh.get_worksheet(0)
        ws.append_row([nick, json.dumps(payload)])
        return True
    except Exception as e:
        st.error(f"Errore DB: {e}")
        return False

# --- 4. CALCOLO CLASSIFICHE (Per i Gironi del Torneo) ---
def update_standings(pref=""):
    groups = get_groups()
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

# --- 5. UI PRINCIPALE E LOGIN ---
# Admin Login in the sidebar to keep top clean
with st.sidebar:
    st.write("### 🔒 Area Riservata Admin")
    code = st.text_input("Password Admin", type="password")
    is_admin = (code == "mondiali2026")

st.markdown("<h1 style='text-align: center; color: #0f172a; margin-bottom: 30px;'>🏆 World Cup 2026 Contest</h1>", unsafe_allow_html=True)

# CAMPO NICKNAME CENTRATO E RISTRETTO
col_spacer1, col_nick, col_spacer2 = st.columns([1, 2, 1])
with col_nick:
    user_name = st.text_input("👤 Nickname Partecipante:", placeholder="Es. Marco88")

st.write("<br>", unsafe_allow_html=True)

if user_name:
    tabs = st.tabs(["🌍 Gironi", "📊 Classifiche", "⚔️ Bracket", "🚀 Invia"] + (["👑 Admin"] if is_admin else []))

    # --- TAB GIRONI ---
    with tabs[0]:
        col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
        with col_btn2:
            if st.button("🪄 Autocompilazione Casuale", use_container_width=True):
                # Aggiornando il session state e chiamando rerun, i widget input si aggiorneranno visivamente
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
                    pts_1 = RANKING[m['h']]
                    pts_2 = RANKING[m['a']]
                    pts_x = (pts_1 + pts_2) // 2
                    
                    with cols[c]:
                        with st.container(border=True):
                            # Badge dei punti basati sul file PDF e Badge Bonus
                            st.markdown(f"""
                            <div class='pts-container'>
                                <span class='pts-badge'>1: {pts_1} pt</span>
                                <span class='pts-badge'>X: {pts_x} pt</span>
                                <span class='pts-badge'>2: {pts_2} pt</span>
                            </div>
                            <span class='bonus-badge'>🎯 +50 pt Risultato Esatto</span>
                            """, unsafe_allow_html=True)
                            
                            c1, in1, vs, in2, c2 = st.columns([1, 1.3, 0.3, 1.3, 1])
                            c1.image(get_flag(m['h']), width=32)
                            
                            # Widget collegato direttamente al session_state tramite la key
                            in1.number_input("H", 0, 9, key=f"h_{idx}", label_visibility="collapsed")
                            
                            vs.markdown("<p style='text-align:center; padding-top:8px; font-weight:bold; color:#94a3b8;'>-</p>", unsafe_allow_html=True)
                            
                            in2.number_input("A", 0, 9, key=f"a_{idx}", label_visibility="collapsed")
                            
                            c2.image(get_flag(m['a']), width=32)
                            
                            st.markdown(f"<p class='team-label'>{m['h']} <span style='color:#94a3b8;'>vs</span> {m['a']}</p>", unsafe_allow_html=True)

    # --- TAB CLASSIFICHE ---
    with tabs[1]:
        st.write("### 📊 Simulazione Classifiche Gironi")
        st.info("Queste classifiche si aggiornano in base ai risultati che hai inserito per comporre il bracket.")
        r, t3, stats = update_standings(pref="")
        
        for i in range(0, 12, 3):
            cs = st.columns(3)
            for k in range(3):
                gid = list(get_groups().keys())[i+k]
                df = pd.DataFrame(stats[gid]).T.sort_values(["Pt", "DR", "GF"], ascending=False)
                cs[k].write(f"**Gruppo {gid}**")
                cs[k].dataframe(df, use_container_width=True)

    # --- TAB BRACKET ---
    def draw_bracket(pref=""):
        r, t3, _ = update_standings(pref)
        th_dict = {row['gr']: row['t'] for _, row in t3.iterrows()}
        
        def match_ui(t1, t2, mid, lbl):
            with st.container(border=True):
                st.caption(lbl)
                l1, r1 = st.columns(2)
                with l1:
                    st.image(get_flag(t1), width=40)
                    if st.button(f"{t1}", key=f"btn_{pref}{mid}_1", use_container_width=True, type="primary" if st.session_state.get(pref+mid)==t1 else "secondary"):
                        st.session_state[pref+mid]=t1; st.rerun()
                with r1:
                    st.image(get_flag(t2), width=40)
                    if st.button(f"{t2}", key=f"btn_{pref}{mid}_2", use_container_width=True, type="primary" if st.session_state.get(pref+mid)==t2 else "secondary"):
                        st.session_state[pref+mid]=t2; st.rerun()
                return st.session_state.get(pref+mid, "TBD")

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.write("📌 **Sedicesimi**")
            v1 = match_ui(r["A"][1], r["C"][1], "S1", "Match 1")
            v2 = match_ui(r["D"][0], th_dict.get("A", "TBD"), "S2", "Match 2")
            # ... Logica nascosta per brevità ma struttura pronta
        with c2:
            st.write("🎯 **Ottavi**")
            v_o1 = match_ui(v1, v2, "O1", "Ottavo 1")
        with c3:
            st.write("💎 **Quarti**")
            v_q1 = match_ui(v_o1, "TBD", "Q1", "Quarto 1")
        with c4:
            st.write("🏆 **Fasi Finali**")
            v_semi = match_ui(v_q1, "TBD", "semi", "Semi 1")
            st.divider()
            win = match_ui(v_semi, "TBD", "winner", "🥇 CAMPIONE")
            st.session_state[pref+"final_winner"] = win
            if win != "TBD" and pref=="": st.balloons()

    with tabs[2]:
        draw_bracket(pref="")

    # --- AREA ADMIN ---
    if is_admin:
        with tabs[-1]:
            st.header("👑 Admin Panel - Gestione Torneo")
            
            c_adm1, c_adm2, c_adm3 = st.columns([1, 2, 1])
            with c_adm2:
                if st.button("🪄 Test: Popola Risultati Ufficiali Casuali", use_container_width=True):
                    for i in range(72):
                        st.session_state[f"adm_h_{i}"] = random.randint(0, 3)
                        st.session_state[f"adm_a_{i}"] = random.randint(0, 3)
                    st.rerun()
            
            st.subheader("1. Inserisci Risultati Ufficiali (Reali)")
            for i, m in enumerate(MATCHES):
                with st.expander(f"G{m['gr']}: {m['h']} vs {m['a']}"):
                    cl1, cl2 = st.columns(2)
                    cl1.number_input(f"Casa ({m['h']})", 0, 9, key=f"adm_h_{i}")
                    cl2.number_input(f"Ospite ({m['a']})", 0, 9, key=f"adm_a_{i}")
            
            st.subheader("2. Bracket Ufficiale (Reale)")
            draw_bracket(pref="adm_")
            
            if st.button("💾 SALVA RISULTATI REALI NEL DATABASE"):
                adm_data = {i: [st.session_state.get(f"adm_h_{i}"), st.session_state.get(f"adm_a_{i}")] for i in range(72)}
                send_to_google("RisultatiReali", "OFFICIAL", adm_data)

    # --- INVIO ---
    with tabs[3]:
        st.write("### 🚀 Ci siamo!")
        if st.button("INVIA I TUOI PRONOSTICI", type="primary", use_container_width=True):
            data = {i: [st.session_state.get(f"h_{i}"), st.session_state.get(f"a_{i}")] for i in range(72)}
            if send_to_google("Pronostici", user_name, {"scores": data, "winner": st.session_state.get("final_winner")}):
                st.success("Tutto salvato correttamente! Buona fortuna!")
