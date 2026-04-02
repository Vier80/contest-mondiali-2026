import streamlit as st
import pandas as pd
import json
import gspread
import random
from google.oauth2.service_account import Credentials

# --- 1. CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="WC 2026 Contest PRO", layout="wide")

# Logo (Placeholder ufficiale FIFA 2026)
LOGO_URL = "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a7/2026_FIFA_World_Cup_logo.svg/1200px-2026_FIFA_World_Cup_logo.svg.png"

# CSS: DARK MODE, TAB GRANDI E LOGIN IN ALTO
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap');
    .stApp { background-color: #0f172a; color: #f8fafc; font-family: 'Inter', sans-serif; }
    
    /* Ingrandimento TAB */
    button[data-baseweb="tab"] p { font-size: 22px !important; font-weight: 800 !important; color: #94a3b8 !important; }
    button[data-baseweb="tab"][aria-selected="true"] p { color: #38bdf8 !important; }
    
    /* Login Admin in alto a dx */
    .admin-login { position: absolute; top: 0; right: 0; padding: 10px; }

    /* Card Partite */
    .match-card { background: #1e293b; border-radius: 12px; padding: 10px; border: 1px solid #334155; margin-bottom: 10px; }
    .ranking-badge { background: #0369a1; color: #e0f2fe; border-radius: 6px; font-size: 11px; font-weight: 800; padding: 3px; text-align: center; margin-bottom: 8px; }
    
    /* Input Numerici */
    input[type="number"] { background-color: #334155 !important; color: white !important; font-size: 20px !important; font-weight: 900 !important; border: 1px solid #475569 !important; text-align: center !important; }
    .team-text { font-size: 12px; font-weight: 700; color: #f1f5f9; text-align: center; }
</style>
""", unsafe_allow_html=True)

# --- 2. DATI E RANKING ---
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
    if not t or t == "???" or t == "Non assegnato": return "https://flagcdn.com/w160/un.png"
    m = {"Messico": "mx", "Sudafrica": "za", "Sudcorea": "kr", "Repubblica Ceca": "cz", "Canada": "ca", "Bosnia Erzegovina": "ba", "Qatar": "qa", "Svizzera": "ch", "Brasile": "br", "Marocco": "ma", "Haiti": "ht", "Scozia": "gb-sct", "USA": "us", "Paraguay": "py", "Australia": "au", "Turchia": "tr", "Germania": "de", "Curacao": "cw", "Costa D'Avorio": "ci", "Ecuador": "ec", "Olanda": "nl", "Giappone": "jp", "Svezia": "se", "Tunisia": "tn", "Belgio": "be", "Egitto": "eg", "Iran": "ir", "Nuova Zelanda": "nz", "Spagna": "es", "Capo Verde": "cv", "Arabia Saudita": "sa", "Uruguay": "uy", "Francia": "fr", "Senegal": "sn", "Iraq": "iq", "Norvegia": "no", "Argentina": "ar", "Algeria": "dz", "Austria": "at", "Giordania": "jo", "Portogallo": "pt", "DR Congo": "cd", "Uzbekistan": "uz", "Colombia": "co", "Inghilterra": "gb-eng", "Croazia": "hr", "Ghana": "gh", "Panama": "pa", "Italia": "it"}
    return f"https://flagcdn.com/w160/{m.get(t, 'un')}.png"

# --- 3. LOGIN ADMIN IN ALTO A DESTRA ---
col_head, col_login = st.columns([7, 3])
with col_head:
    st.image(LOGO_URL, width=180)
with col_login:
    st.write("")
    admin_pw = st.text_input("🔓 Login Admin", type="password", placeholder="Password...")
    is_admin = (admin_pw == "mondiali2026")

# --- 4. LOGICA CLASSICHE ---
def calcola_classifiche():
    res = {g: {t: {"Pt": 0, "DR": 0, "GF": 0} for t in ts} for g, ts in G_TEAMS.items()}
    for i, m in enumerate(MATCHES):
        h_val = st.session_state.get(f"h_{i}", 0)
        a_val = st.session_state.get(f"a_{i}", 0)
        sh, sa = res[m['gr']][m['h']], res[m['gr']][m['a']]
        sh["GF"] += h_val; sa["GF"] += a_val
        sh["DR"] += (h_val - a_val); sa["DR"] += (a_val - h_val)
        if h_val > a_val: sh["Pt"] += 3
        elif a_val > h_val: sa["Pt"] += 3
        else: sh["Pt"] += 1; sa["Pt"] += 1
    
    final_ranks = {}
    thirds = []
    for gid, ts in res.items():
        df = pd.DataFrame(ts).T.sort_values(["Pt", "DR", "GF"], ascending=False)
        final_ranks[gid] = df.index.tolist()
        thirds.append({"team": df.index[2], "Pt": df.iloc[2]["Pt"], "DR": df.iloc[2]["DR"], "GF": df.iloc[2]["GF"], "gr": gid})
    
    best_thirds = pd.DataFrame(thirds).sort_values(["Pt", "DR", "GF"], ascending=False).head(8)
    return final_ranks, best_thirds, res

def get_3rd_team(slot, th_dict):
    disponibili = sorted(th_dict.keys())
    mapping = {"1D": 0, "1B": 1, "1A": 2, "1C": 3, "1G": 4, "1I": 5, "1K": 6, "1L": 7}
    idx = mapping.get(slot, 0)
    gr_key = disponibili[idx] if idx < len(disponibili) else "???"
    return th_dict.get(gr_key, "Non assegnato")

# --- 5. FUNZIONE SALVATAGGIO ---
def salva_su_google(tab, nick, payload):
    try:
        info = json.loads(st.secrets["service_account"])
        creds = Credentials.from_service_account_info(info, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
        client = gspread.authorize(creds)
        URL_FOGLIO = "" # <--- INCOLLA IL TUO LINK GOOGLE SHEETS
        sh = client.open_by_url(URL_FOGLIO)
        try: ws = sh.worksheet(tab)
        except: ws = sh.get_worksheet(0)
        ws.append_row([nick, json.dumps(payload)])
        return True
    except Exception as e:
        st.error(f"Errore connessione: {e}")
        return False

# --- 6. INTERFACCIA UTENTE ---
user_nick = st.text_input("👤 Inserisci il tuo Nickname per iniziare:", placeholder="Es. Marco88")

if user_nick:
    t_labels = ["🌍 Gironi", "📊 Classifiche", "⚔️ Bracket", "🚀 Invia"]
    if is_admin: t_labels.append("⚙️ Area Admin")
    tabs = st.tabs(t_labels)

    # --- TAB GIRONI ---
    with tabs[0]:
        st.write("### 🏟️ Fase a Gironi")
        if st.button("🪄 Compila Random (User)"):
            for i in range(72):
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
                            st.markdown(f"<div class='ranking-badge'>Punti: 1={p1} | X={px} | 2={p2}</div>", unsafe_allow_html=True)
                            c_f1, c_in1, c_vs, c_in2, c_f2 = st.columns([1, 1.5, 0.4, 1.5, 1])
                            c_f1.image(get_flag(m['h']), width=30)
                            st.session_state[f"h_{idx}"] = c_in1.number_input("H", 0, 9, key=f"nh_{idx}", value=st.session_state.get(f"h_{idx}", 0), label_visibility="collapsed")
                            c_vs.markdown("<p style='padding-top:8px; font-weight:900;'>–</p>", unsafe_allow_html=True)
                            st.session_state[f"a_{idx}"] = c_in2.number_input("A", 0, 9, key=f"na_{idx}", value=st.session_state.get(f"a_{idx}", 0), label_visibility="collapsed")
                            c_f2.image(get_flag(m['a']), width=30)
                            st.markdown(f"<div class='team-text'>{m['h']} vs {m['a']}</div>", unsafe_allow_html=True)

    # --- TAB CLASSIFICHE ---
    with tabs[1]:
        ranks, b_thirds_df, stats = calcola_classifiche()
        st.write("### 📊 Classifiche Gruppi")
        for i in range(0, 12, 3):
            cols = st.columns(3)
            for k in range(3):
                gid = list(G_TEAMS.keys())[i+k]
                df = pd.DataFrame(stats[gid]).T.sort_values(["Pt", "DR", "GF"], ascending=False)
                cols[k].dataframe(df, use_container_width=True)
        st.divider()
        st.write("### 🏁 Migliori Terze")
        st.table(b_thirds_df)

    # --- TAB BRACKET (TENNISTICO SX-DX) ---
    with tabs[2]:
        ranks, th_df, _ = calcola_classifiche()
        th_dict = {row['gr']: row['team'] for _, row in th_df.iterrows()}
        
        def render_compact(t1, t2, mid, lbl):
            with st.container(border=True):
                st.caption(lbl)
                c1, c2 = st.columns(2)
                with c1:
                    st.image(get_flag(t1), width=40)
                    if st.button(f"{t1}", key=f"kb1_{mid}", use_container_width=True, type="primary" if st.session_state.get(mid)==t1 else "secondary"):
                        st.session_state[mid]=t1; st.rerun()
                with c2:
                    st.image(get_flag(t2), width=40)
                    if st.button(f"{t2}", key=f"kb2_{mid}", use_container_width=True, type="primary" if st.session_state.get(mid)==t2 else "secondary"):
                        st.session_state[mid]=t2; st.rerun()
                return st.session_state.get(mid, "???")

        col_sed, col_ott, col_qua, col_fin = st.columns([1, 1, 1, 1.3])
        
        with col_sed:
            st.write("📌 Sedicesimi")
            v_s1 = render_compact(ranks["A"][1], ranks["C"][1], "S1", "M1")
            v_s2 = render_compact(ranks["D"][0], get_3rd_team("1D", th_dict), "S2", "M2")
        with col_ott:
            st.write("🎯 Ottavi")
            v_o1 = render_compact(v_s1, v_s2, "O1", "Ottavo 1")
        with col_qua:
            st.write("💎 Quarti")
            v_q1 = render_compact(v_o1, "TBD", "Q1", "Quarto 1")
        with col_fin:
            st.write("🔥 Semi & Finale")
            v_semi1 = render_compact(v_q1, "TBD", "semi1", "Semi 1")
            st.divider()
            campione = render_compact(v_semi1, "TBD", "f_camp", "🏆 CAMPIONE")
            st.session_state["campione"] = campione
            if campione != "???" and campione != "": st.balloons()

    # --- TAB AREA ADMIN ---
    if is_admin:
        with tabs[-1]:
            st.header("⚙️ Area Admin - Risultati Ufficiali")
            if st.button("🪄 Auto-compila Risultati Admin (Test)"):
                for i in range(72):
                    st.session_state[f"adm_h_{i}"] = random.randint(0, 3)
                    st.session_state[f"adm_a_{i}"] = random.randint(0, 3)
                st.rerun()
            
            for i, m in enumerate(MATCHES):
                with st.expander(f"G{m['gr']}: {m['h']} vs {m['a']}"):
                    c1, c2 = st.columns(2)
                    st.session_state[f"adm_h_{i}"] = c1.number_input("H", 0,9, key=f"ah_{i}", value=st.session_state.get(f"adm_h_{i}",0))
                    st.session_state[f"adm_a_{i}"] = c2.number_input("A", 0,9, key=f"aa_{i}", value=st.session_state.get(f"adm_a_{i}",0))
            
            if st.button("💾 SALVA RISULTATI ADMIN"):
                d = {i: [st.session_state.get(f"adm_h_{i}"), st.session_state.get(f"adm_a_{i}")] for i in range(72)}
                salva_su_google("RisultatiReali", "OFFICIAL_ADMIN", d)

    # --- TAB INVIO ---
    with tabs[3]:
        if st.button("🚀 INVIA PRONOSTICI DEFINITIVAMENTE", type="primary", use_container_width=True):
            gironi = {f"M_{i}": [st.session_state.get(f"h_{i}",0), st.session_state.get(f"a_{i}",0)] for i in range(72)}
            if salva_su_google("Pronostici", user_nick, {"gironi": gironi, "campione": st.session_state.get("campione")}):
                st.balloons(); st.success("Inviato con successo!")
