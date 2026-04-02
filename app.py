import streamlit as st
import pandas as pd
import json
import gspread
import random
from google.oauth2.service_account import Credentials

# --- 1. CONFIGURAZIONE PAGINA E STYLE ---
st.set_page_config(page_title="World Cup 2026 Prediction Contest", layout="wide")

# CSS DARK MODE & UI
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap');
    .stApp { background-color: #0f172a; color: #f8fafc; font-family: 'Inter', sans-serif; }
    
    /* Ingrandimento TAB */
    button[data-baseweb="tab"] p { font-size: 24px !important; font-weight: 800 !important; }
    button[data-baseweb="tab"] { height: 70px !important; }
    
    /* Card Partite */
    .match-card { background: #1e293b; border-radius: 15px; padding: 15px; border: 1px solid #334155; margin-bottom: 10px; }
    .ranking-badge { background: #0369a1; color: #e0f2fe; border-radius: 6px; font-size: 11px; font-weight: 800; padding: 4px; text-align: center; margin-bottom: 10px; }
    
    /* Input Numerici */
    input[type="number"] { background-color: #334155 !important; color: white !important; font-size: 22px !important; font-weight: 900 !important; border: 1px solid #475569 !important; border-radius: 8px !important; }
    
    .team-text { font-size: 13px; font-weight: 700; color: #f1f5f9; text-align: center; }
</style>
""", unsafe_allow_html=True)

# --- 2. DATABASE E LOGO ---
LOGO_URL = "https://upload.wikimedia.org/wikipedia/it/thumb/d/d3/FIFA_World_Cup_2026_logo.svg/1200px-FIFA_World_Cup_2026_logo.svg.png"

RANKING = {
    "Messico": 15, "Sudafrica": 61, "Sudcorea": 22, "Repubblica Ceca": 44, "Canada": 27, "Bosnia Erzegovina": 71, "Qatar": 58, "Svizzera": 17,
    "Brasile": 5, "Marocco": 11, "Haiti": 84, "Scozia": 36, "USA": 14, "Paraguay": 39, "Australia": 26, "Turchia": 25, "Germania": 9, "Curacao": 82,
    "Costa D'Avorio": 42, "Ecuador": 23, "Olanda": 7, "Giappone": 18, "Svezia": 43, "Tunisia": 40, "Belgio": 8, "Egitto": 34, "Iran": 20, 
    "Nuova Zelanda": 86, "Spagna": 1, "Capo Verde": 68, "Arabia Saudita": 60, "Uruguay": 16, "Francia": 3, "Senegal": 19, "Iraq": 58, 
    "Norvegia": 29, "Argentina": 2, "Algeria": 35, "Austria": 24, "Giordania": 66, "Portogallo": 6, "DR Congo": 56, "Uzbekistan": 50, 
    "Colombia": 13, "Inghilterra": 4, "Croazia": 10, "Ghana": 72, "Panama": 30, "Italia": 13
}

@st.cache_data
def get_data():
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

G_TEAMS, MATCHES = get_data()

def get_flag(t):
    if not t or t == "???": return "https://flagcdn.com/w160/un.png"
    m = {"Messico": "mx", "Sudafrica": "za", "Sudcorea": "kr", "Repubblica Ceca": "cz", "Canada": "ca", "Bosnia Erzegovina": "ba", "Qatar": "qa", "Svizzera": "ch", "Brasile": "br", "Marocco": "ma", "Haiti": "ht", "Scozia": "gb-sct", "USA": "us", "Paraguay": "py", "Australia": "au", "Turchia": "tr", "Germania": "de", "Curacao": "cw", "Costa D'Avorio": "ci", "Ecuador": "ec", "Olanda": "nl", "Giappone": "jp", "Svezia": "se", "Tunisia": "tn", "Belgio": "be", "Egitto": "eg", "Iran": "ir", "Nuova Zelanda": "nz", "Spagna": "es", "Capo Verde": "cv", "Arabia Saudita": "sa", "Uruguay": "uy", "Francia": "fr", "Senegal": "sn", "Iraq": "iq", "Norvegia": "no", "Argentina": "ar", "Algeria": "dz", "Austria": "at", "Giordania": "jo", "Portogallo": "pt", "DR Congo": "cd", "Uzbekistan": "uz", "Colombia": "co", "Inghilterra": "gb-eng", "Croazia": "hr", "Ghana": "gh", "Panama": "pa", "Italia": "it"}
    return f"https://flagcdn.com/w160/{m.get(t, 'un')}.png"

# --- 3. GOOGLE SHEETS CONNECTION ---
def get_gsheet_client():
    info = json.loads(st.secrets["service_account"])
    creds = Credentials.from_service_account_info(info, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
    return gspread.authorize(creds), info['client_email']

def salva_dati(tab_name, nick, payload):
    try:
        client, email = get_gsheet_client()
        URL = "https://docs.google.com/spreadsheets/d/1palUSBw4IlBFzU4dKtgT0tnjPiPEtxIc6K-DK05vXG8/edit?gid=0#gid=0" # <--- INSERISCI URL QUI
        sh = client.open_by_url(URL)
        try: ws = sh.worksheet(tab_name)
        except: ws = sh.get_worksheet(0)
        ws.append_row([nick, json.dumps(payload)])
        return True
    except Exception as e:
        st.error(f"Errore 403/Connessione: {e}. Verifica permessi Editor per {email}")
        return False

# --- 4. LOGICA ---
def calcola_classifiche(prefix=""):
    res = {g: {t: {"Pt": 0, "DR": 0, "GF": 0} for t in ts} for g, ts in G_TEAMS.items()}
    for i, m in enumerate(MATCHES):
        h = st.session_state.get(f"{prefix}h_{i}", 0)
        a = st.session_state.get(f"{prefix}a_{i}", 0)
        sh, sa = res[m['gr']][m['h']], res[m['gr']][m['a']]
        sh["GF"] += h; sa["GF"] += a; sh["DR"] += (h - a); sa["DR"] += (a - h)
        if h > a: sh["Pt"] += 3
        elif a > h: sa["Pt"] += 3
        else: sh["Pt"] += 1; sa["Pt"] += 1
    final_ranks = {}
    thirds = []
    for gid, ts in res.items():
        df = pd.DataFrame(ts).T.sort_values(["Pt", "DR", "GF"], ascending=False)
        final_ranks[gid] = df.index.tolist()
        thirds.append({"team": df.index[2], "Pt": df.iloc[2]["Pt"], "gr": gid})
    return final_ranks, pd.DataFrame(thirds).sort_values("Pt", ascending=False).head(8), res

# --- 5. INTERFACCIA ---
st.image(LOGO_URL, width=120)
st.title("FIFA World Cup 2026 Contest")

# Login Admin rapido
with st.sidebar:
    adm_key = st.text_input("🔑 Admin Access", type="password")
    is_admin = (adm_key == "mondiali2026")

user_nick = st.text_input("👤 Inserisci il tuo Nickname per partecipare:", placeholder="Esempio: Bomber99")

if user_nick:
    t_labels = ["🌍 Gironi", "📊 Classifiche", "⚔️ Bracket", "🚀 Invia"]
    if is_admin: t_labels.append("⚙️ Admin Panel")
    tabs = st.tabs(t_labels)

    with tabs[0]:
        st.write("### 🏟️ Inserimento Pronostici")
        if st.button("🪄 Compila Random (Test)"):
            for i in range(72):
                st.session_state[f"h_{i}"] = random.randint(0, 3)
                st.session_state[f"a_{i}"] = random.randint(0, 3)
            st.rerun()

        for r in range(18):
            cols = st.columns(4)
            for c in range(4):
                idx = r * 4 + c
                if idx < 72:
                    m = MATCHES[idx]
                    p1, p2, px = RANKING[m['a']], RANKING[m['h']], (RANKING[m['h']]+RANKING[m['a']])//2
                    with cols[c]:
                        with st.container(border=True):
                            st.markdown(f"<div class='ranking-badge'>Punti: 1={p1} | X={px} | 2={p2}</div>", unsafe_allow_html=True)
                            # --- SCORE ORIZZONTALE ---
                            sc = st.columns([1, 1.2, 0.4, 1.2, 1])
                            sc[0].image(get_flag(m['h']), width=30)
                            st.session_state[f"h_{idx}"] = sc[1].number_input("H", 0, 9, key=f"nh_{idx}", value=st.session_state.get(f"h_{idx}", 0), label_visibility="collapsed")
                            sc[2].markdown("<p style='padding-top:8px;'>–</p>", unsafe_allow_html=True)
                            st.session_state[f"a_{idx}"] = sc[3].number_input("A", 0, 9, key=f"na_{idx}", value=st.session_state.get(f"a_{idx}", 0), label_visibility="collapsed")
                            sc[4].image(get_flag(m['a']), width=30)
                            st.markdown(f"<div class='team-text'>{m['h']} vs {m['a']}</div>", unsafe_allow_html=True)

    with tabs[2]:
        ranks, th_df, _ = calcola_classifiche()
        th_dict = {row['gr']: row['team'] for _, row in th_df.iterrows()}
        def get_3(s):
            m = {"1D":0,"1B":1,"1A":2,"1C":3,"1G":4,"1I":5,"1K":6,"1L":7}
            return th_dict.get(sorted(th_dict.keys())[m.get(s,0)] if m.get(s,0)<len(th_dict) else "A", "???")

        def ren_match(t1, t2, mid, lbl):
            with st.container(border=True):
                st.caption(lbl)
                c1, c2 = st.columns(2)
                with c1:
                    st.image(get_flag(t1), width=35)
                    if st.button(f"{t1}", key=f"b1_{mid}", use_container_width=True, type="primary" if st.session_state.get(mid)==t1 else "secondary"):
                        st.session_state[mid]=t1; st.rerun()
                with c2:
                    st.image(get_flag(t2), width=35)
                    if st.button(f"{t2}", key=f"b2_{mid}", use_container_width=True, type="primary" if st.session_state.get(mid)==t2 else "secondary"):
                        st.session_state[mid]=t2; st.rerun()
                return st.session_state.get(mid, "???")

        # BRACKET SX -> DX
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.write("🏁 Sedicesimi")
            v_s1 = ren_match(ranks["A"][1], ranks["C"][1], "S1", "M1")
            v_s2 = ren_match(ranks["D"][0], get_3( "1D"), "S2", "M2")
        with c2:
            st.write("🎯 Ottavi")
            v_o1 = ren_match(v_s1, v_s2, "O1", "Ottavo 1")
        with c3:
            st.write("💎 Quarti")
            v_q1 = ren_match(v_o1, "Vinc. O2", "Q1", "Quarto 1")
        with c4:
            st.write("🏆 Semi & Finale")
            v_semi1 = ren_match(v_q1, "Vinc. Q2", "semi1", "Semi 1")
            st.divider()
            campione = ren_match(v_semi1, "Finalista 2", "f_c", "CAMPIONE")
            st.session_state["campione"] = campione

    with tabs[4] if is_admin else st.empty():
        if is_admin:
            st.header("⚙️ Pannello Risultati Reali & Classifica")
            if st.button("🪄 Auto-fill Risultati Admin"):
                for i in range(72):
                    st.session_state[f"adm_h_{i}"] = random.randint(0, 3)
                    st.session_state[f"adm_a_{i}"] = random.randint(0, 3)
                st.rerun()
            
            # Elenco 72 partite
            for i, m in enumerate(MATCHES):
                with st.expander(f"Match {i+1}: {m['h']} vs {m['a']}"):
                    a1, a2 = st.columns(2)
                    st.session_state[f"adm_h_{i}"] = a1.number_input("Casa", 0,9, key=f"ah_{i}", value=st.session_state.get(f"adm_h_{i}",0))
                    st.session_state[f"adm_a_{i}"] = a2.number_input("Ospite", 0,9, key=f"aa_{i}", value=st.session_state.get(f"adm_a_{i}",0))
            
            if st.button("💾 SALVA RISULTATI REALI"):
                d = {i: [st.session_state.get(f"adm_h_{i}"), st.session_state.get(f"adm_a_{i}")] for i in range(72)}
                salva_dati("RisultatiReali", "ADMIN", d)
            
            st.divider()
            st.subheader("📊 Classifica Partecipanti")
            st.info("Qui vedrai i punti di tutti i partecipanti confrontando i loro pronostici con i risultati reali inseriti sopra.")
            # Nota: In produzione qui si legge il foglio 'Pronostici' e si calcolano i punti.

    with tabs[3]:
        if st.button("🚀 INVIA PRONOSTICI"):
            data = {i: [st.session_state.get(f"h_{i}"), st.session_state.get(f"a_{i}")] for i in range(72)}
            if salva_dati("Pronostici", user_nick, {"g": data, "v": st.session_state.get("campione")}):
                st.balloons(); st.success("Inviato!")
