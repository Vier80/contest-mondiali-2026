import streamlit as st
import pandas as pd
import json
import gspread
import random
from google.oauth2.service_account import Credentials

# --- 1. CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="WC 2026 Contest PRO", layout="wide")

# CSS: TAB Grandi, Score Orizzontale e UI
st.markdown("""
<style>
    /* Ingrandimento TAB */
    button[data-baseweb="tab"] p { font-size: 22px !important; font-weight: 800 !important; color: #1e293b !important; }
    .stApp { background-color: #f4f7f9; }
    .match-card { background: white; border-radius: 12px; padding: 10px; border: 1px solid #e2e8f0; margin-bottom: 10px; }
    .ranking-badge { 
        background: #fee2e2; color: #991b1b; border: 1px solid #fecaca; 
        border-radius: 6px; font-size: 10px; font-weight: 800; padding: 2px; text-align: center; margin-bottom: 5px;
    }
    input[type="number"] { font-size: 22px !important; font-weight: 900 !important; text-align: center !important; }
    .team-text { font-size: 12px; font-weight: 700; color: #1e293b; text-align: center; }
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
    if t == "???" or t == "": return "https://flagcdn.com/w160/un.png"
    m = {
        "Messico": "mx", "Sudafrica": "za", "Sudcorea": "kr", "Repubblica Ceca": "cz", "Canada": "ca", "Bosnia Erzegovina": "ba",
        "Qatar": "qa", "Svizzera": "ch", "Brasile": "br", "Marocco": "ma", "Haiti": "ht", "Scozia": "gb-sct", "USA": "us",
        "Paraguay": "py", "Australia": "au", "Turchia": "tr", "Germania": "de", "Curacao": "cw", "Costa D'Avorio": "ci",
        "Ecuador": "ec", "Olanda": "nl", "Giappone": "jp", "Svezia": "se", "Tunisia": "tn", "Belgio": "be", "Egitto": "eg",
        "Iran": "ir", "Nuova Zelanda": "nz", "Spagna": "es", "Capo Verde": "cv", "Arabia Saudita": "sa", "Uruguay": "uy",
        "Francia": "fr", "Senegal": "sn", "Iraq": "iq", "Norvegia": "no", "Argentina": "ar", "Algeria": "dz", "Austria": "at",
        "Giordania": "jo", "Portogallo": "pt", "DR Congo": "cd", "Uzbekistan": "uz", "Colombia": "co", "Inghilterra": "gb-eng",
        "Croazia": "hr", "Ghana": "gh", "Panama": "pa", "Italia": "it"
    }
    return f"https://flagcdn.com/w160/{m.get(t, 'un')}.png"

# --- 3. LOGICA DATABASE ---
def salva_su_google(nome_foglio, nick, dati):
    try:
        info = json.loads(st.secrets["service_account"])
        creds = Credentials.from_service_account_info(info, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
        client = gspread.authorize(creds)
        # --- SOSTITUISCI CON IL TUO URL ---
        URL_FOGLIO = "https://docs.google.com/spreadsheets/d/1palUSBw4IlBFzU4dKtgT0tnjPiPEtxIc6K-DK05vXG8/edit?gid=0#gid=0"
        sheet = client.open_by_url(URL_FOGLIO).worksheet(nome_foglio)
        sheet.append_row([nick, json.dumps(dati)])
        return True
    except Exception as e:
        st.error(f"ERRORE GOOGLE: {e}")
        return False

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
    for gid, ts in res.items():
        df = pd.DataFrame(ts).T.sort_values(["Pt", "DR", "GF"], ascending=False)
        final_ranks[gid] = df.index.tolist()
        thirds.append({"team": df.index[2], "Pt": df.iloc[2]["Pt"], "DR": df.iloc[2]["DR"], "GF": df.iloc[2]["GF"], "gr": gid})
    return final_ranks, pd.DataFrame(thirds).sort_values(["Pt", "DR", "GF"], ascending=False).head(8), res

def get_3rd_team(slot, th_dict):
    disponibili = sorted(th_dict.keys())
    mapping = {"1D": 0, "1B": 1, "1A": 2, "1C": 3, "1G": 4, "1I": 5, "1K": 6, "1L": 7}
    idx = mapping.get(slot, 0)
    gr = disponibili[idx] if idx < len(disponibili) else "A"
    return th_dict.get(gr, "TBD")

# --- 4. INTERFACCIA ---
c_top1, c_top2 = st.columns([8, 2])
with c_top2:
    pw = st.text_input("🔑 Admin", type="password")
    is_admin = (pw == "mondiali2026")

user_nick = st.text_input("👤 Nickname Partecipante:", placeholder="Inserisci il tuo nome...")

if user_nick:
    tab_labels = ["🌍 Gironi", "📊 Classifiche", "⚔️ Bracket", "🚀 Invia"]
    if is_admin: tab_labels.append("⚙️ Area Admin")
    t1, t2, t3, t4, *adm = st.tabs(tab_labels)

    # --- TAB GIRONI ---
    with t1:
        if st.button("🪄 Compila Random"):
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
                            st.markdown(f"<div class='ranking-badge'>1: {p1} | X: {px} | 2: {p2}</div>", unsafe_allow_html=True)
                            # SCORE ORIZZONTALE
                            sc1, sc2, sc3, sc4, sc5 = st.columns([1, 1.2, 0.4, 1.2, 1])
                            with sc1: st.image(get_flag(m['h']), width=35)
                            with sc2: st.number_input("H", 0, 9, key=f"h_{idx}", value=st.session_state.get(f"h_{idx}", 0), label_visibility="collapsed")
                            with sc3: st.markdown("<div style='text-align:center;font-weight:bold;padding-top:8px;'>-</div>", unsafe_allow_html=True)
                            with sc4: st.number_input("A", 0, 9, key=f"a_{idx}", value=st.session_state.get(f"a_{idx}", 0), label_visibility="collapsed")
                            with sc5: st.image(get_flag(m['a']), width=35)
                            st.markdown(f"<div class='team-text'>{m['h']} vs {m['a']}</div>", unsafe_allow_html=True)

    # --- TAB CLASSIFICHE ---
    with t2:
        ranks, th_df, stats = calcola_classifiche()
        for i in range(0, 12, 3):
            cs = st.columns(3)
            for k in range(3):
                gid = list(G_TEAMS.keys())[i+k]
                df = pd.DataFrame(stats[gid]).T.sort_values(["Pt", "DR", "GF"], ascending=False)
                cs[k].write(f"**Gruppo {gid}**"); cs[k].dataframe(df, use_container_width=True)

    # --- TAB BRACKET ---
    with t3:
        ranks, th_df, _ = calcola_classifiche()
        th_dict = {row['gr']: row['team'] for _, row in th_df.iterrows()}
        
        def render_match(t1, t2, mid, label):
            with st.container(border=True):
                st.caption(label)
                col1, col2 = st.columns(2)
                with col1:
                    st.image(get_flag(t1), width=45)
                    if st.button(f"{t1}", key=f"btn1_{mid}", use_container_width=True, type="primary" if st.session_state.get(mid) == t1 else "secondary"):
                        st.session_state[mid] = t1
                        st.rerun()
                with col2:
                    st.image(get_flag(t2), width=45)
                    if st.button(f"{t2}", key=f"btn2_{mid}", use_container_width=True, type="primary" if st.session_state.get(mid) == t2 else "secondary"):
                        st.session_state[mid] = t2
                        st.rerun()
                return st.session_state.get(mid, "???")

        st.subheader("🏁 Sedicesimi")
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
        v_s = {m[0]: render_match(m[1], m[2], m[0], f"Match {m[0]}") for m in s_matches}

        st.subheader("🎯 Ottavi")
        o_pairs = [("S1","S2"), ("S3","S4"), ("S5","S6"), ("S7","S8"), ("S9","S10"), ("S11","S12"), ("S13","S14"), ("S15","S16")]
        v_o = {f"O{i}": render_match(v_s[p[0]], v_s[p[1]], f"mo_{i}", f"Ottavo {i+1}") for i, p in enumerate(o_pairs)}

        st.subheader("💎 Quarti")
        q_pairs = [("O0","O1"), ("O2","O3"), ("O4","O5"), ("O6","O7")]
        v_q = {f"Q{i}": render_match(v_o[p[0]], v_o[p[1]], f"mq_{i}", f"Quarto {i+1}") for i, p in enumerate(q_pairs)}

        st.subheader("🔥 Semifinali e Finale")
        c_semi = st.columns(2)
        with c_semi[0]: v_semi1 = render_match(v_q["Q0"], v_q["Q1"], "semi1", "Semi 1")
        with c_semi[1]: v_semi2 = render_match(v_q["Q2"], v_q["Q3"], "semi2", "Semi 2")
        
        st.divider()
        st.subheader("🥇 FINALISSIMA")
        f_col = st.columns([1, 2, 1])[1]
        with f_col:
            campione = render_match(v_semi1, v_semi2, "f_c", "FINALE")
            st.session_state["campione"] = campione
            if campione != "???" and campione != "": st.balloons()

    # --- TAB INVIO ---
    with tab4:
        if st.button("🚀 SALVA TUTTO DEFINITIVAMENTE", type="primary", use_container_width=True):
            gironi_data = {f"M_{i}": [st.session_state.get(f"h_{i}"), st.session_state.get(f"a_{i}")] for i in range(72)}
            if salva_su_google("Pronostici", user_nick, {"gironi": gironi_data, "vincitore": st.session_state.get("campione")}):
                st.success("Pronostici inviati con successo!")

    # --- TAB ADMIN ---
    if is_admin:
        with adm[0]:
            st.header("⚙️ Area Risultati Reali")
            for i, m in enumerate(MATCHES):
                with st.expander(f"{m['h']} vs {m['a']}"):
                    c1, c2 = st.columns(2)
                    st.number_input("Casa", 0, 9, key=f"adm_h_{i}")
                    st.number_input("Ospite", 0, 9, key=f"adm_a_{i}")
            if st.button("SALVA RISULTATI UFFICIALI"):
                adm_data = {i: [st.session_state[f"adm_h_{i}"], st.session_state[f"adm_a_{i}"]] for i in range(72)}
                salva_su_google("RisultatiReali", "ADMIN", adm_data)
                st.success("Risultati reali salvati!")
