import streamlit as st
import pandas as pd
import json
import gspread
import random
from google.oauth2.service_account import Credentials

# --- 1. CONFIGURAZIONE PAGINA & LOGO ---
st.set_page_config(page_title="FIFA World Cup 2026 - Contest Admin", layout="wide")

# Logo ufficiale (Placeholder - sostituisci con URL reale se necessario)
LOGO_URL = "https://upload.wikimedia.org/wikipedia/it/thumb/d/d3/FIFA_World_Cup_2026_logo.svg/1200px-FIFA_World_Cup_2026_logo.svg.png"

# CSS: STILE DARK & UI MIGLIORATA
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;800&display=swap');
    
    .stApp {{ background-color: #0f172a; color: #f8fafc; font-family: 'Poppins', sans-serif; }}
    
    /* Ingrandimento TAB */
    button[data-baseweb="tab"] p {{ font-size: 20px !important; font-weight: 800 !important; color: #94a3b8 !important; }}
    button[data-baseweb="tab"][aria-selected="true"] p {{ color: #38bdf8 !important; }}

    /* Card Partite Dark */
    .match-card {{
        background: #1e293b; border-radius: 12px; padding: 15px; border: 1px solid #334155; margin-bottom: 12px;
    }}
    
    /* Badge Ranking */
    .ranking-badge {{
        background: #0ea5e9; color: white; border-radius: 6px; font-size: 11px; font-weight: 800;
        padding: 4px; text-align: center; margin-bottom: 10px;
    }}

    /* Input Numerici */
    input[type="number"] {{
        background-color: #334155 !important; color: white !important;
        font-size: 22px !important; font-weight: 900 !important; border: 1px solid #475569 !important;
    }}
    
    .team-name {{ font-size: 13px; font-weight: 600; color: #f1f5f9; text-align: center; }}
</style>
""", unsafe_allow_html=True)

# --- 2. DATABASE RANKING ---
RANKING = {{
    "Messico": 15, "Sudafrica": 61, "Sudcorea": 22, "Repubblica Ceca": 44, "Canada": 27, "Bosnia Erzegovina": 71, "Qatar": 58, "Svizzera": 17,
    "Brasile": 5, "Marocco": 11, "Haiti": 84, "Scozia": 36, "USA": 14, "Paraguay": 39, "Australia": 26, "Turchia": 25, "Germania": 9, "Curacao": 82,
    "Costa D'Avorio": 42, "Ecuador": 23, "Olanda": 7, "Giappone": 18, "Svezia": 43, "Tunisia": 40, "Belgio": 8, "Egitto": 34, "Iran": 20, 
    "Nuova Zelanda": 86, "Spagna": 1, "Capo Verde": 68, "Arabia Saudita": 60, "Uruguay": 16, "Francia": 3, "Senegal": 19, "Iraq": 58, 
    "Norvegia": 29, "Argentina": 2, "Algeria": 35, "Austria": 24, "Giordania": 66, "Portogallo": 6, "DR Congo": 56, "Uzbekistan": 50, 
    "Colombia": 13, "Inghilterra": 4, "Croazia": 10, "Ghana": 72, "Panama": 30, "Italia": 13
}}

@st.cache_data
def get_data():
    g = {{
        "A": ["Messico", "Sudafrica", "Sudcorea", "Repubblica Ceca"], "B": ["Canada", "Bosnia Erzegovina", "Qatar", "Svizzera"],
        "C": ["Brasile", "Marocco", "Haiti", "Scozia"], "D": ["USA", "Paraguay", "Australia", "Turchia"],
        "E": ["Germania", "Curacao", "Costa D'Avorio", "Ecuador"], "F": ["Olanda", "Giappone", "Svezia", "Tunisia"],
        "G": ["Belgio", "Egitto", "Iran", "Nuova Zelanda"], "H": ["Spagna", "Capo Verde", "Arabia Saudita", "Uruguay"],
        "I": ["Francia", "Senegal", "Iraq", "Norvegia"], "J": ["Argentina", "Algeria", "Austria", "Giordania"],
        "K": ["Portogallo", "DR Congo", "Uzbekistan", "Colombia"], "L": ["Inghilterra", "Croazia", "Ghana", "Panama"]
    }}
    ml = []
    for gid, teams in g.items():
        for h, a in [(0, 1), (2, 3), (0, 2), (1, 3), (0, 3), (1, 2)]:
            ml.append({{"gr": gid, "h": teams[h], "a": teams[a]}})
    return g, ml

G_TEAMS, MATCHES = get_data()

def get_flag(t):
    if not t or t == "???": return "https://flagcdn.com/w160/un.png"
    m = {{
        "Messico": "mx", "Sudafrica": "za", "Sudcorea": "kr", "Repubblica Ceca": "cz", "Canada": "ca", "Bosnia Erzegovina": "ba",
        "Qatar": "qa", "Svizzera": "ch", "Brasile": "br", "Marocco": "ma", "Haiti": "ht", "Scozia": "gb-sct", "USA": "us",
        "Paraguay": "py", "Australia": "au", "Turchia": "tr", "Germania": "de", "Curacao": "cw", "Costa D'Avorio": "ci",
        "Ecuador": "ec", "Olanda": "nl", "Giappone": "jp", "Svezia": "se", "Tunisia": "tn", "Belgio": "be", "Egitto": "eg",
        "Iran": "ir", "Nuova Zelanda": "nz", "Spagna": "es", "Capo Verde": "cv", "Arabia Saudita": "sa", "Uruguay": "uy",
        "Francia": "fr", "Senegal": "sn", "Iraq": "iq", "Norvegia": "no", "Argentina": "ar", "Algeria": "dz", "Austria": "at",
        "Giordania": "jo", "Portogallo": "pt", "DR Congo": "cd", "Uzbekistan": "uz", "Colombia": "co", "Inghilterra": "gb-eng",
        "Croazia": "hr", "Ghana": "gh", "Panama": "pa", "Italia": "it"
    }}
    return f"https://flagcdn.com/w160/{{m.get(t, 'un')}}.png"

# --- 3. LOGICA DATABASE (DEFINITIVA) ---
def salva_su_google(tab_name, nick, dati):
    try:
        info = json.loads(st.secrets["service_account"])
        creds = Credentials.from_service_account_info(info, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
        client = gspread.authorize(creds)
        
        # LINK DEL TUO FOGLIO (Assicurati che sia corretto!)
        URL_FOGLIO = "https://docs.google.com/spreadsheets/d/1palUSBw4IlBFzU4dKtgT0tnjPiPEtxIc6K-DK05vXG8/edit?gid=0#gid=0"
        
        # Pulizia URL per estrarre l'ID (più affidabile)
        if "spreadsheets/d/" in URL_FOGLIO:
            id_foglio = URL_FOGLIO.split("spreadsheets/d/")[1].split("/")[0]
            sh = client.open_by_key(id_foglio)
        else:
            sh = client.open_by_url(URL_FOGLIO)
            
        # Prova ad aprire il foglio richiesto, altrimenti usa il primo
        try:
            ws = sh.worksheet(tab_name)
        except:
            ws = sh.get_worksheet(0)
            
        ws.append_row([nick, json.dumps(dati)])
        return True
    except Exception as e:
        st.error(f"❌ Errore Google Sheets: {{e}}")
        st.info(f"💡 ASSICURATI DI AVER CONDIVISO IL FOGLIO CON: {{info['client_email']}}")
        return False

# --- 4. FUNZIONI CALCOLO ---
def calcola_classifiche():
    res = {{g: {{t: {{"Pt": 0, "DR": 0, "GF": 0}} for t in ts}} for g, ts in G_TEAMS.items()}}
    for i, m in enumerate(MATCHES):
        h_g = st.session_state.get(f"h_{{i}}", 0)
        a_g = st.session_state.get(f"a_{{i}}", 0)
        sh, sa = res[m['gr']][m['h']], res[m['gr']][m['a']]
        sh["GF"] += h_g; sa["GF"] += a_g
        sh["DR"] += (h_g - a_g); sa["DR"] += (a_g - h_g)
        if h_g > a_g: sh["Pt"] += 3
        elif a_g > h_g: sa["Pt"] += 3
        else: sh["Pt"] += 1; sa["Pt"] += 1
    
    final_ranks = {{}}
    thirds = []
    for gid, ts in res.items():
        df = pd.DataFrame(ts).T.sort_values(["Pt", "DR", "GF"], ascending=False)
        final_ranks[gid] = df.index.tolist()
        thirds.append({{"team": df.index[2], "Pt": df.iloc[2]["Pt"], "gr": gid}})
    return final_ranks, pd.DataFrame(thirds).sort_values(["Pt"], ascending=False).head(8), res

def get_3rd(slot, th_dict):
    disponibili = sorted(th_dict.keys())
    mapping = {{"1D": 0, "1B": 1, "1A": 2, "1C": 3, "1G": 4, "1I": 5, "1K": 6, "1L": 7}}
    idx = mapping.get(slot, 0)
    gr = disponibili[idx] if idx < len(disponibili) else "A"
    return th_dict.get(gr, "???")

# --- 5. LOGICA LOGIN ADMIN ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

# --- 6. INTERFACCIA ---
col_l, col_r = st.columns([8, 2])
with col_l: st.image(LOGO_URL, width=150)
with col_r:
    admin_pw = st.text_input("🔑 Admin Login", type="password")
    if admin_pw == "mondiali2026": st.session_state.logged_in = True

user_nick = st.text_input("👤 Nome Partecipante:", placeholder="Inserisci il tuo nome...")

if user_nick:
    tab_titles = ["🌍 Gironi", "📊 Classifiche", "⚔️ Bracket", "🚀 Invia"]
    if st.session_state.logged_in: tab_titles.append("⚙️ Area Admin")
    
    tabs = st.tabs(tab_titles)

    # --- TAB GIRONI ---
    with tabs[0]:
        if st.button("🪄 Compila Random (Partecipante)"):
            for i in range(72):
                st.session_state[f"h_{{i}}"] = random.randint(0, 3)
                st.session_state[f"a_{{i}}"] = random.randint(0, 3)
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
                            st.markdown(f"<div class='ranking-badge'>1: {{p1}} | X: {{px}} | 2: {{p2}}</div>", unsafe_allow_html=True)
                            col_score = st.columns([1, 1.2, 0.4, 1.2, 1])
                            col_score[0].image(get_flag(m['h']), width=30)
                            st.session_state[f"h_{{idx}}"] = col_score[1].number_input("H", 0, 9, key=f"nh_{{idx}}", value=st.session_state.get(f"h_{{idx}}", 0), label_visibility="collapsed")
                            col_score[2].markdown("<p style='padding-top:8px;'>–</p>", unsafe_allow_html=True)
                            st.session_state[f"a_{{idx}}"] = col_score[3].number_input("A", 0, 9, key=f"na_{{idx}}", value=st.session_state.get(f"a_{{idx}}", 0), label_visibility="collapsed")
                            col_score[4].image(get_flag(m['a']), width=30)
                            st.markdown(f"<div class='team-name'>{{m['h']}} vs {{m['a']}}</div>", unsafe_allow_html=True)

    # --- TAB BRACKET (TENNISTICO SX-DX) ---
    with tabs[2]:
        ranks, th_df, _ = calcola_classifiche()
        th_dict = {{row['gr']: row['team'] for _, row in th_df.iterrows()}}
        
        def draw_match(t1, t2, mid, label):
            with st.container(border=True):
                st.caption(label)
                c1, c2 = st.columns(2)
                with c1:
                    st.image(get_flag(t1), width=40)
                    if st.button(f"{{t1}}", key=f"b1_{{mid}}", type="primary" if st.session_state.get(mid) == t1 else "secondary", use_container_width=True):
                        st.session_state[mid] = t1; st.rerun()
                with c2:
                    st.image(get_flag(t2), width=40)
                    if st.button(f"{{t2}}", key=f"b2_{{mid}}", type="primary" if st.session_state.get(mid) == t2 else "secondary", use_container_width=True):
                        st.session_state[mid] = t2; st.rerun()
                return st.session_state.get(mid, "???")

        # Layout Tennistico
        cs, co, cq, cf = st.columns([1.2, 1, 1, 1.3])
        
        with cs:
            st.write("🏁 Sedicesimi")
            # Accoppiamenti completi...
            v_s1 = draw_match(ranks["A"][1], ranks["C"][1], "S1", "M1")
            v_s2 = draw_match(ranks["D"][0], get_3rd("1D", th_dict), "S2", "M2")
            # (Aggiungi gli altri sedicesimi qui seguendo lo stesso schema)

        with co:
            st.write("🎯 Ottavi")
            v_o1 = draw_match(v_s1, v_s2, "O1", "Ottavo 1")

        with cq:
            st.write("💎 Quarti")
            v_q1 = draw_match(v_o1, "Vinc. O2", "Q1", "Quarto 1")

        with cf:
            st.write("🔥 Semi & Finale")
            v_semi1 = draw_match(v_q1, "Vinc. Q2", "semi1", "Semi 1")
            st.divider()
            campione = draw_match(v_semi1, "Vinc. S2", "f_c", "🏆 CAMPIONE")
            st.session_state["campione"] = campione

    # --- TAB AREA ADMIN (LOGIN PROTETTO) ---
    if st.session_state.logged_in:
        with tabs[-1]:
            st.header("⚙️ Pannello Gestione Risultati Reali")
            if st.button("🪄 TEST: Compila Automaticamente Risultati Admin"):
                for i in range(72):
                    st.session_state[f"adm_h_{{i}}"] = random.randint(0, 3)
                    st.session_state[f"adm_a_{{i}}"] = random.randint(0, 3)
                st.rerun()
            
            for i, m in enumerate(MATCHES):
                with st.expander(f"Girone {{m['gr']}}: {{m['h']}} vs {{m['a']}}"):
                    ca1, ca2 = st.columns(2)
                    st.session_state[f"adm_h_{{i}}"] = ca1.number_input("H", 0, 9, key=f"ah_{{i}}", value=st.session_state.get(f"adm_h_{{i}}", 0))
                    st.session_state[f"adm_a_{{i}}"] = ca2.number_input("A", 0, 9, key=f"aa_{{i}}", value=st.session_state.get(f"adm_a_{{i}}", 0))
            
            if st.button("💾 SALVA RISULTATI UFFICIALI NEL DATABASE"):
                adm_data = {{i: [st.session_state.get(f"adm_h_{{i}}"), st.session_state.get(f"adm_a_{{i}}")] for i in range(72)}}
                if salva_su_google("RisultatiReali", "ADMIN_OFFICIAL", adm_data):
                    st.success("Risultati Ufficiali Salvati con Successo!")

    # --- TAB INVIO ---
    with tabs[3]:
        if st.button("🚀 INVIA I TUOI PRONOSTICI DEFINITIVAMENTE", type="primary", use_container_width=True):
            user_data = {{i: [st.session_state.get(f"h_{{i}}"), st.session_state.get(f"a_{{i}}")] for i in range(72)}}
            if salva_su_google("Pronostici", user_nick, {{"gironi": user_data, "campione": st.session_state.get("campione")}}):
                st.balloons(); st.success("Inviato!")
