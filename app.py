import streamlit as st
import pandas as pd
import json
import gspread
import random
from google.oauth2.service_account import Credentials

# --- 1. CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="WC 2026 Contest PRO", layout="wide")

# CSS: Look moderno, card pulite e input centrati
st.markdown("""
<style>
    .stApp { background-color: #f4f7f9; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { 
        background-color: #ffffff; border-radius: 5px 5px 0 0; padding: 10px 20px; border: 1px solid #e0e0e0;
    }
    .match-card { background: white; border-radius: 12px; padding: 15px; border: 1px solid #e2e8f0; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); }
    .ranking-badge { 
        background: #fee2e2; color: #991b1b; border: 1px solid #fecaca; 
        border-radius: 6px; font-size: 11px; font-weight: 800; padding: 4px; text-align: center; margin-bottom: 10px;
    }
    input[type="number"] { font-size: 22px !important; font-weight: 900 !important; text-align: center !important; }
    .team-name { font-size: 13px; font-weight: 700; color: #1e293b; text-align: center; line-height: 1.2; }
</style>
""", unsafe_allow_html=True)

# --- 2. DATABASE E DATI ---
RANKING = {
    "Messico": 15, "Sudafrica": 61, "Sudcorea": 22, "Repubblica Ceca": 44,
    "Canada": 27, "Bosnia Erzegovina": 71, "Qatar": 58, "Svizzera": 17,
    "Brasile": 5, "Marocco": 11, "Haiti": 84, "Scozia": 36,
    "USA": 14, "Paraguay": 39, "Australia": 26, "Turchia": 25,
    "Germania": 9, "Curacao": 82, "Costa D'Avorio": 42, "Ecuador": 23,
    "Olanda": 7, "Giappone": 18, "Svezia": 43, "Tunisia": 40,
    "Belgio": 8, "Egitto": 34, "Iran": 20, "Nuova Zelanda": 86,
    "Spagna": 1, "Capo Verde": 68, "Arabia Saudita": 60, "Uruguay": 16,
    "Francia": 3, "Senegal": 19, "Iraq": 58, "Norvegia": 29,
    "Argentina": 2, "Algeria": 35, "Austria": 24, "Giordania": 66,
    "Portogallo": 6, "DR Congo": 56, "Uzbekistan": 50, "Colombia": 13,
    "Inghilterra": 4, "Croazia": 10, "Ghana": 72, "Panama": 30, "Italia": 13
}

@st.cache_data
def get_data():
    g = {
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
    ml = []
    for gid, teams in g.items():
        pairs = [(0, 1), (2, 3), (0, 2), (1, 3), (0, 3), (1, 2)]
        for h, a in pairs:
            ml.append({"gr": gid, "h": teams[h], "a": teams[a]})
    return g, ml

G_TEAMS, MATCHES = get_data()

def get_flag(t):
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

# --- 3. LOGICA CALCOLO ---
def calcola_classifiche():
    res = {g: {t: {"Pt": 0, "DR": 0, "GF": 0} for t in ts} for g, ts in G_TEAMS.items()}
    for i, m in enumerate(MATCHES):
        h_g = st.session_state.get(f"h_{i}", 0)
        a_g = st.session_state.get(f"a_{i}", 0)
        sh, sa = res[m['gr']][m['h']], res[m['gr']][m['a']]
        sh["GF"] += h_g; sa["GF"] += a_g
        sh["DR"] += (h_g - a_g); sa["DR"] += (a_g - h_g)
        if h_g > a_g: sh["Pt"] += 3
        elif a_g > h_g: sa["Pt"] += 3
        else: sh["Pt"] += 1; sa["Pt"] += 1
    
    final_ranks = {}
    thirds = []
    for gid, teams_stat in res.items():
        df = pd.DataFrame(teams_stat).T.sort_values(["Pt", "DR", "GF"], ascending=False)
        final_ranks[gid] = df.index.tolist()
        thirds.append({"team": df.index[2], "Pt": df.iloc[2]["Pt"], "DR": df.iloc[2]["DR"], "GF": df.iloc[2]["GF"], "gr": gid})
    
    best_thirds = pd.DataFrame(thirds).sort_values(["Pt", "DR", "GF"], ascending=False).head(8)
    return final_ranks, best_thirds, res

def get_3rd_team(slot, b_thirds_dict):
    disponibili = sorted(b_thirds_dict.keys())
    mapping = {"1D": 0, "1B": 1, "1A": 2, "1C": 3, "1G": 4, "1I": 5, "1K": 6, "1L": 7}
    idx = mapping.get(slot, 0)
    gr = disponibili[idx] if idx < len(disponibili) else disponibili[-1]
    return b_thirds_dict.get(gr, "TBD")

def salva_su_google(nick, dati):
    try:
        js = json.loads(st.secrets["service_account"])
        creds = Credentials.from_service_account_info(js, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
        client = gspread.authorize(creds)
        
        # --- INCOLLA QUI IL TUO LINK ---
        URL_FOGLIO = "https://docs.google.com/spreadsheets/d/1palUSBw4IlBFzU4dKtgT0tnjPiPEtxIc6K-DK05vXG8/edit?gid=0#gid=0" 
        
        sheet = client.open_by_url(URL_FOGLIO).sheet1
        sheet.append_row([nick, json.dumps(dati)])
        return True
    except Exception as e:
        st.error(f"Errore tecnico: {e}")
        return False

# --- 4. INTERFACCIA ---
st.title("🏆 FIFA World Cup 2026 Prediction Contest")
user_nick = st.text_input("👤 Inserisci il tuo Nickname:", placeholder="Es. Luca_King")

if user_nick:
    tab1, tab2, tab3, tab4 = st.tabs(["🌍 Gironi", "📊 Classifiche", "⚔️ Bracket", "🚀 Invia"])

    with tab1:
        st.write("### 🏟️ Fase a Gironi")
        if st.button("🪄 Compilazione Rapida (Random)"):
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
                    p1, p2 = RANKING[m['a']], RANKING[m['h']]
                    px = (p1 + p2) // 2
                    with cols[c]:
                        with st.container(border=True):
                            st.markdown(f"<div class='ranking-badge'>1: {p1} | X: {px} | 2: {p2}</div>", unsafe_allow_html=True)
                            c1, c_vs, c2 = st.columns([2, 1, 2])
                            c1.image(get_flag(m['h']), width=40)
                            c2.image(get_flag(m['a']), width=40)
                            c1.markdown(f"<div class='team-name'>{m['h']}</div>", unsafe_allow_html=True)
                            c2.markdown(f"<div class='team-name'>{m['a']}</div>", unsafe_allow_html=True)
                            
                            i1, i2 = st.columns(2)
                            # FISSIAMO LE CHIAVI PER LA COMPILAZIONE AUTOMATICA
                            st.number_input("H", 0, 9, key=f"h_{idx}", label_visibility="collapsed")
                            st.number_input("A", 0, 9, key=f"a_{idx}", label_visibility="collapsed")

    with tab2:
        ranks, b_thirds, stats = calcola_classifiche()
        st.header("Classifiche")
        for i in range(0, 12, 3):
            cs = st.columns(3)
            for k in range(3):
                gid = list(G_TEAMS.keys())[i+k]
                df = pd.DataFrame(stats[gid]).T.sort_values(["Pt", "DR", "GF"], ascending=False)
                cs[k].write(f"**Gruppo {gid}**")
                cs[k].dataframe(df, use_container_width=True)
        st.divider()
        st.subheader("Migliori Terze")
        st.table(b_thirds)

    with tab3:
        ranks, b_thirds_df, _ = calcola_classifiche()
        th_dict = {row['gr']: row['team'] for _, row in b_thirds_df.iterrows()}
        
        # --- SEDICESIMI ---
        st.subheader("🏁 Sedicesimi di Finale")
        s_matches = [
            ("S1", ranks["A"][1], ranks["C"][1]), ("S2", ranks["D"][0], get_3rd_team("1D", th_dict)),
            ("S3", ranks["B"][0], get_3rd_team("1B", th_dict)), ("S4", ranks["F"][0], ranks["E"][1]),
            ("S5", ranks["B"][1], ranks["F"][1]), ("S6", ranks["A"][0], get_3rd_team("1A", th_dict)),
            ("S7", ranks["E"][0], ranks["D"][1]), ("S8", ranks["C"][0], get_3rd_team("1C", th_dict)),
            ("S9", ranks["G"][0], ranks["I"][1]), ("S10", ranks["H"][0], ranks["J"][1]),
            ("S11", ranks["I"][0], get_3rd_team("1I", th_dict)), ("S12", ranks["J"][0], ranks["L"][1]),
            ("S13", ranks["K"][0], get_3rd_team("1K", th_dict)), ("S14", ranks["L"][0], ranks["G"][1]),
            ("S15", ranks["G"][1], ranks["H"][1]), ("S16", ranks["K"][1], get_3rd_team("1L", th_dict))
        ]
        
        v_s = {}
        c_s = st.columns(4)
        for i, (m_id, t1, t2) in enumerate(s_matches):
            with c_s[i // 4]:
                with st.container(border=True):
                    st.markdown(f"**Match {i+1}**")
                    st.image([get_flag(t1), get_flag(t2)], width=35)
                    v_s[m_id] = st.radio(f"Vince:", [t1, t2], key=f"vs_{m_id}", horizontal=True)

        # --- OTTAVI ---
        st.subheader("🎯 Ottavi di Finale")
        o_pairs = [("S1","S2"), ("S3","S4"), ("S5","S6"), ("S7","S8"), ("S9","S10"), ("S11","S12"), ("S13","S14"), ("S15","S16")]
        v_o = {}
        c_o = st.columns(4)
        for i, (m1, m2) in enumerate(o_pairs):
            with c_o[i // 2]:
                with st.container(border=True):
                    t1, t2 = v_s[m1], v_s[m2]
                    st.image([get_flag(t1), get_flag(t2)], width=35)
                    v_o[f"O{i}"] = st.radio(f"Ottavo {i+1}", [t1, t2], key=f"vo_{i}")

        # --- QUARTI ---
        st.subheader("💎 Quarti di Finale")
        q_pairs = [("O0","O1"), ("O2","O3"), ("O4","O5"), ("O6","O7")]
        v_q = {}
        c_q = st.columns(4)
        for i, (m1, m2) in enumerate(q_pairs):
            with c_q[i]:
                with st.container(border=True):
                    t1, t2 = v_o[m1], v_o[m2]
                    st.image([get_flag(t1), get_flag(t2)], width=35)
                    v_q[f"Q{i}"] = st.radio(f"Quarto {i+1}", [t1, t2], key=f"vq_{i}")

        # --- SEMI & FINALE ---
        st.subheader("🔥 Fasi Finali")
        c_semi = st.columns(2)
        v_semi1 = c_semi[0].radio("Semi 1", [v_q["Q0"], v_q["Q1"]], key="semi1")
        v_semi2 = c_semi[1].radio("Semi 2", [v_q["Q2"], v_q["Q3"]], key="semi2")
        
        st.divider()
        v_finale = st.selectbox("🏆 CAMPIONE DEL MONDO 2026", [v_semi1, v_semi2])
        st.image(get_flag(v_finale), width=100)
        st.session_state["campione"] = v_finale

    with tab4:
        st.header("Invia i Pronostici")
        if st.button("SALVA DEFINITIVAMENTE", type="primary"):
            # RACCOLTA DATI CORRETTA DALLE CHIAVI WIDGET
            dati = {
                "Gironi": {f"M_{i}": [st.session_state.get(f"h_{i}", 0), st.session_state.get(f"a_{i}", 0)] for i in range(72)},
                "Campione": st.session_state.get("campione", "Non assegnato")
            }
            if salva_su_google(user_nick, dati):
                st.balloons()
                st.success("Pronostici salvati su Google Sheets! Buona fortuna!")
