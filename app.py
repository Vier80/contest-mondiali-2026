import streamlit as st
import pandas as pd
import json
import gspread
import random
from google.oauth2.service_account import Credentials

# --- 1. CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="WC 2026 Prediction PRO", layout="wide")

# CSS: STILE DARK PROFESSIONALE AD ALTO CONTRASTO
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap');
    .stApp { background-color: #0b0f1a; color: #ffffff; font-family: 'Inter', sans-serif; }
    
    /* Ingrandimento TAB */
    button[data-baseweb="tab"] p { font-size: 22px !important; font-weight: 800 !important; color: #94a3b8 !important; }
    button[data-baseweb="tab"][aria-selected="true"] p { color: #00d4ff !important; }

    /* Card Partite */
    .match-card {
        background: #1e293b; border-radius: 12px; padding: 15px; 
        border: 1px solid #334155; margin-bottom: 12px;
    }
    
    /* Badge Punti 1X2 */
    .ranking-badge {
        background: #0ea5e9; color: white; border-radius: 6px; font-size: 11px; font-weight: 800;
        padding: 4px; text-align: center; margin-bottom: 10px;
    }

    /* Input Numerici Bianchi su Sfondo Scuro */
    input[type="number"] {
        background-color: #0f172a !important; color: #ffffff !important;
        font-size: 22px !important; font-weight: 900 !important; 
        border: 2px solid #38bdf8 !important; text-align: center !important;
    }
    
    .team-label { font-size: 14px; font-weight: 700; color: #f8fafc; text-align: center; }
    .vs-text { color: #64748b; font-weight: 900; font-size: 20px; }
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

# --- 3. LOGICA DATABASE (SISTEMATA) ---
def salva_dati(tab_name, nick, payload):
    try:
        info = json.loads(st.secrets["service_account"])
        creds = Credentials.from_service_account_info(info, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
        client = gspread.authorize(creds)
        URL_FOGLIO = "https://docs.google.com/spreadsheets/d/1palUSBw4IlBFzU4dKtgT0tnjPiPEtxIc6K-DK05vXG8/edit?gid=0#gid=0"
        
        # Estrazione ID per evitare errori di URL
        sheet_id = URL_FOGLIO.split("/d/")[1].split("/")[0] if "/d/" in URL_FOGLIO else URL_FOGLIO
        sh = client.open_by_key(sheet_id)
        
        try: ws = sh.worksheet(tab_name)
        except: ws = sh.get_worksheet(0)
            
        ws.append_row([nick, json.dumps(payload)])
        return True
    except Exception as e:
        st.error(f"❌ Errore Google Sheets: {e}")
        st.info(f"Assicurati di aver condiviso il file come EDITOR con: {info['client_email']}")
        return False

# --- 4. LOGIN E LOGO IN ALTO ---
c_logo, c_adm = st.columns([7, 3])
with c_logo:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/a/a7/2026_FIFA_World_Cup_logo.svg/512px-2026_FIFA_World_Cup_logo.svg.png", width=120)
with c_adm:
    st.write("### 🔒 Area Admin")
    pass_admin = st.text_input("Password", type="password", label_visibility="collapsed")
    is_admin = (pass_admin == "mondiali2026")

user_nick = st.text_input("👤 Nome Partecipante:", placeholder="Inserisci il tuo Nickname...")

if user_nick:
    t_labels = ["🌍 Gironi", "📊 Classifiche", "⚔️ Bracket", "🚀 Invia"]
    if is_admin: t_labels.append("👑 Admin Dashboard")
    tabs = st.tabs(t_labels)

    # --- TAB GIRONI ---
    with tabs[0]:
        if st.button("🪄 Compilazione Automatica Risultati"):
            for i in range(len(MATCHES)):
                st.session_state[f"h_{i}"] = random.randint(0, 4)
                st.session_state[f"a_{i}"] = random.randint(0, 4)
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
                            st.markdown(f"<div class='ranking-badge'>PUNTI: 1={p1} | X={px} | 2={p2}</div>", unsafe_allow_html=True)
                            s_col = st.columns([1, 1.2, 0.4, 1.2, 1])
                            s_col[0].image(get_flag(m['h']), width=30)
                            st.session_state[f"h_{idx}"] = s_col[1].number_input("H", 0, 9, key=f"in_h_{idx}", value=st.session_state.get(f"h_{idx}", 0), label_visibility="collapsed")
                            s_col[2].markdown("<p style='text-align:center; padding-top:8px;'>–</p>", unsafe_allow_html=True)
                            st.session_state[f"a_{idx}"] = s_col[3].number_input("A", 0, 9, key=f"in_a_{idx}", value=st.session_state.get(f"a_{idx}", 0), label_visibility="collapsed")
                            s_col[4].image(get_flag(m['a']), width=30)
                            st.markdown(f"<p class='team-label'>{m['h']} vs {m['a']}</p>", unsafe_allow_html=True)

    # --- TAB CLASSIFICHE ---
    with tabs[1]:
        st.write("### 📊 Classifiche Gruppi")
        stats = {g: {t: {"Pt": 0, "DR": 0} for t in ts} for g, ts in get_groups().items()}
        for i, m in enumerate(MATCHES):
            h, a = st.session_state.get(f"h_{i}", 0), st.session_state.get(f"a_{i}", 0)
            sh, sa = stats[m['gr']][m['h']], stats[m['gr']][m['a']]
            sh["DR"] += (h - a); sa["DR"] += (a - h)
            if h > a: sh["Pt"] += 3
            elif a > h: sa["Pt"] += 3
            else: sh["Pt"] += 1; sa["Pt"] += 1
        
        ranks = {g: pd.DataFrame(ts).T.sort_values(["Pt", "DR"], ascending=False) for g, ts in stats.items()}
        for i in range(0, 12, 3):
            cs = st.columns(3)
            for k in range(3):
                gid = list(get_groups().keys())[i+k]
                cs[k].write(f"**Gruppo {gid}**")
                cs[k].dataframe(ranks[gid], use_container_width=True)

    # --- TAB BRACKET TENNISTICO ---
    with tabs[2]:
        def render_b(t1, t2, mid, lbl):
            with st.container(border=True):
                st.caption(lbl)
                c1, c2 = st.columns(2)
                with c1:
                    st.image(get_flag(t1), width=35)
                    if st.button(f"{t1}", key=f"bt1_{mid}", use_container_width=True, type="primary" if st.session_state.get(mid)==t1 else "secondary"):
                        st.session_state[mid]=t1; st.rerun()
                with c2:
                    st.image(get_flag(t2), width=35)
                    if st.button(f"{t2}", key=f"bt2_{mid}", use_container_width=True, type="primary" if st.session_state.get(mid)==t2 else "secondary"):
                        st.session_state[mid]=t2; st.rerun()
                return st.session_state.get(mid, "TBD")

        if st.button("🪄 Autocompila Bracket"):
            all_teams = list(RANKING.keys())
            for k in ["S1","S2","O1","semi1","vincitore"]: st.session_state[k] = random.choice(all_teams)
            st.rerun()

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.write("Sedicesimi")
            v_s1 = render_b("TBD", "TBD", "S1", "M1")
            v_s2 = render_b("TBD", "TBD", "S2", "M2")
        with c2:
            st.write("Ottavi")
            v_o1 = render_b(v_s1, v_s2, "O1", "Ottavo 1")
        with c3:
            st.write("Quarti")
            v_q1 = render_b(v_o1, "TBD", "Q1", "Quarto 1")
        with c4:
            st.write("Semi & Finale")
            v_s1 = render_b(v_q1, "TBD", "semi1", "Semi 1")
            st.divider()
            win = render_b(v_s1, "TBD", "vincitore", "🏆 CAMPIONE")
            st.session_state["campione_finale"] = win
            if win != "TBD": st.balloons()

    # --- TAB ADMIN ---
    if is_admin:
        with tabs[-1]:
            st.header("⚙️ Area Admin - Controllo Totale")
            if st.button("🪄 Test: Compila Automaticamente Risultati Reali"):
                for i in range(72): st.session_state[f"adm_h_{i}"] = random.randint(0, 3)
                for i in range(72): st.session_state[f"adm_a_{i}"] = random.randint(0, 3)
                st.rerun()
            
            st.subheader("Classifica Partecipanti")
            st.dataframe(pd.DataFrame({"Utente": ["User1", "User2"], "Punti": [150, 110]}))
            
            with st.expander("Modifica Risultati Ufficiali (72 Partite)"):
                for i, m in enumerate(MATCHES):
                    c1, c2 = st.columns(2)
                    st.session_state[f"adm_h_{i}"] = c1.number_input(f"{m['h']}", 0, 9, key=f"ah_{i}", value=st.session_state.get(f"adm_h_{i}", 0))
                    st.session_state[f"adm_a_{i}"] = c2.number_input(f"{m['a']}", 0, 9, key=f"aa_{i}", value=st.session_state.get(f"adm_a_{i}", 0))

    # --- TAB INVIO ---
    with tabs[3]:
        if st.button("🚀 INVIA PRONOSTICI", type="primary", use_container_width=True):
            d = {i: [st.session_state.get(f"h_{i}"), st.session_state.get(f"a_{i}")] for i in range(72)}
            if salva_dati("Pronostici", user_nick, {"g": d, "v": st.session_state.get("campione_finale")}):
                st.success("Pronostici salvati!")
