import streamlit as st
import pandas as pd
import json
import gspread
import random
from google.oauth2.service_account import Credentials

# --- 1. SETTINGS & DARK UI (MOCKUP STYLE) ---
st.set_page_config(page_title="WC 2026 Contest", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #1e2129; color: white; }
    .match-card {
        background-color: #2d313d;
        border-radius: 15px;
        padding: 20px;
        text-align: center;
        border: 1px solid #3d4250;
        height: 300px;
        display: flex; flex-direction: column; justify-content: space-between;
    }
    .group-header { color: #ff4b4b; font-weight: 800; font-size: 14px; text-transform: uppercase; margin-bottom: 10px; }
    .team-name { font-size: 20px !important; font-weight: 700 !important; color: #ffffff; height: 50px; display: flex; align-items: center; justify-content: center; }
    .pts-info { font-size: 14px; color: #aeb4c2; background: #3d4250; padding: 5px; border-radius: 8px; margin-top: 10px; }
    .stNumberInput input { background-color: #1e2129 !important; color: white !important; font-size: 22px !important; border: 1px solid #ff4b4b !important; }
    .btn-compila { background-color: #ff4b4b !important; color: white !important; border-radius: 10px !important; font-weight: bold !important; padding: 15px !important; }
    /* Sidebar styling */
    section[data-testid="stSidebar"] { background-color: #2d313d !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATA (RANKING & FLAGS) ---
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

def get_flag(t):
    m = {"Messico": "mx", "Sudafrica": "za", "Sudcorea": "kr", "Repubblica Ceca": "cz", "Canada": "ca", "Bosnia Erzegovina": "ba", "Qatar": "qa", "Svizzera": "ch", "Brasile": "br", "Marocco": "ma", "Haiti": "ht", "Scozia": "gb-sct", "USA": "us", "Paraguay": "py", "Australia": "au", "Turchia": "tr", "Germania": "de", "Curacao": "cw", "Costa D'Avorio": "ci", "Ecuador": "ec", "Olanda": "nl", "Giappone": "jp", "Svezia": "se", "Tunisia": "tn", "Belgio": "be", "Egitto": "eg", "Iran": "ir", "Nuova Zelanda": "nz", "Spagna": "es", "Capo Verde": "cv", "Arabia Saudita": "sa", "Uruguay": "uy", "Francia": "fr", "Senegal": "sn", "Iraq": "iq", "Norvegia": "no", "Argentina": "ar", "Algeria": "dz", "Austria": "at", "Giordania": "jo", "Portogallo": "pt", "DR Congo": "cd", "Uzbekistan": "uz", "Colombia": "co", "Inghilterra": "gb-eng", "Croazia": "hr", "Ghana": "gh", "Panama": "pa", "Italia": "it"}
    return f"https://flagcdn.com/w160/{m.get(t, 'un')}.png"

# --- 3. LOGICA CALCOLO BRACKET (IL CERVELLO) ---
def get_bracket_teams(standings):
    # 1. Vincitrici e Seconde
    winners = {g: df.index[0] for g, df in standings.items()}
    runners = {g: df.index[1] for g, df in standings.items()}
    
    # 2. Migliori Terze
    thirds = []
    for g, df in standings.items():
        t_data = df.iloc[2]
        thirds.append({"team": df.index[2], "pt": t_data["Pt"], "dr": t_data["DR"], "gf": t_data["GF"], "gr": g})
    
    best_8 = pd.DataFrame(thirds).sort_values(["pt","dr","gf"], ascending=False).head(8)
    set_gr = set(best_3_gr := best_8["gr"].tolist())
    
    # Matrice Terze Semplificata (basata su regolebracket.rtf)
    # Mapping slot -> 3rd place team
    m_thirds = {t["gr"]: t["team"] for idx, t in best_8.iterrows()}
    
    return winners, runners, m_thirds

# --- 4. INTERFACCIA ---
with st.sidebar:
    st.image(get_flag("Italia"), width=100)
    nick = st.text_input("NICKNAME", placeholder="Bomber88")
    st.write("---")
    adm = st.text_input("🔑 ADMIN", type="password")

if not nick:
    st.title("🏆 World Cup 2026 Contest")
    st.warning("Inserisci il tuo Nickname nella barra laterale per iniziare!")
else:
    t_gironi, t_cl, t_bracket, t_invio = st.tabs(["🌍 Gironi", "📊 Classifiche", "⚔️ Bracket", "🚀 Invia"])

    # Caricamento Gironi
    g_raw = {"A":["Messico","Sudafrica","Sudcorea","Repubblica Ceca"], "B":["Canada","Bosnia Erzegovina","Qatar","Svizzera"], "C":["Brasile","Marocco","Haiti","Scozia"], "D":["USA","Paraguay","Australia","Turchia"], "E":["Germania","Curacao","Costa D'Avorio","Ecuador"], "F":["Olanda","Giappone","Svezia","Tunisia"], "G":["Belgio","Egitto","Iran","Nuova Zelanda"], "H":["Spagna","Capo Verde","Arabia Saudita","Uruguay"], "I":["Francia","Senegal","Iraq","Norvegia"], "J":["Argentina","Algeria","Austria","Giordania"], "K":["Portogallo","DR Congo","Uzbekistan","Colombia"], "L":["Inghilterra","Croazia","Ghana","Panama"]}
    matches = []
    for g, ts in g_raw.items():
        for h, a in [(0,1), (2,3), (0,2), (1,3), (0,3), (1,2)]:
            matches.append({"gr": g, "h": ts[h], "a": ts[a]})

    with t_gironi:
        st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
        if st.button("Compila Automaticamente", key="auto_fill"):
            for i in range(72):
                st.session_state[f"h_{i}"] = random.randint(0, 3)
                st.session_state[f"a_{i}"] = random.randint(0, 3)
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

        for r in range(0, 72, 4):
            cols = st.columns(4)
            for c in range(4):
                idx = r + c
                if idx < 72:
                    m = matches[idx]
                    p1, p2 = RANKING[m['a']], RANKING[m['h']]
                    with cols[c]:
                        st.markdown(f'<div class="match-card"><div class="group-header">GIRONE {m["gr"]}</div>', unsafe_allow_html=True)
                        c1, c2, c3 = st.columns([1, 0.3, 1])
                        with c1:
                            st.image(get_flag(m['h']), width=55)
                            st.markdown(f'<div class="team-name">{m["h"]}</div>', unsafe_allow_html=True)
                            h_v = st.number_input("H", 0, 9, key=f"h_{idx}", label_visibility="collapsed")
                        with c2: st.markdown('<div class="vs-text" style="margin-top:40px;">VS</div>', unsafe_allow_html=True)
                        with c3:
                            st.image(get_flag(m['a']), width=55)
                            st.markdown(f'<div class="team-name">{m["a"]}</div>', unsafe_allow_html=True)
                            a_v = st.number_input("A", 0, 9, key=f"a_{idx}", label_visibility="collapsed")
                        st.markdown(f'<div class="pts-info">Punti: 1: {p1} | X: {(p1+p2)//2} | 2: {p2}</div></div>', unsafe_allow_html=True)

    # CALCOLO CLASSIFICHE PER BRACKET
    standings = {}
    for g, teams in g_raw.items():
        df = pd.DataFrame(0, index=teams, columns=["Pt", "DR", "GF"])
        for i, m in enumerate(matches):
            if m["gr"] == g:
                hg, ag = st.session_state.get(f"h_{i}", 0), st.session_state.get(f"a_{i}", 0)
                df.at[m["h"], "GF"] += hg; df.at[m["a"], "GF"] += ag
                df.at[m["h"], "DR"] += (hg-ag); df.at[m["a"], "DR"] += (ag-hg)
                if hg > ag: df.at[m["h"], "Pt"] += 3
                elif ag > hg: df.at[m["a"], "Pt"] += 3
                else: df.at[m["h"], "Pt"] += 1; df.at[m["a"], "Pt"] += 1
        standings[g] = df.sort_values(["Pt", "DR", "GF"], ascending=False)

    with t_cl:
        for i in range(0, 12, 3):
            cols = st.columns(3)
            for j in range(3):
                g_id = list(standings.keys())[i+j]
                with cols[j]:
                    st.subheader(f"Gruppo {g_id}")
                    st.dataframe(standings[g_id], use_container_width=True)

    with t_bracket:
        st.header("⚔️ Sedicesimi di Finale (Auto-popolati)")
        win, run, th = get_bracket_teams(standings)
        
        # Gli accoppiamenti dal tuo file RTF
        b_cols = st.columns(2)
        with b_cols[0]:
            st.info(f"Ottavo 1: (2A) {run['A']} vs (2C) {run['C']}")
            res1 = st.selectbox("Vince O1", [run['A'], run['C']], key="res1")
            
            # Qui la logica delle terze basata su matrice
            terza_match2 = list(th.values())[0] if th else "3° D/E/F"
            st.info(f"Ottavo 2: (1D) {win['D']} vs (3°) {terza_match2}")
            res2 = st.selectbox("Vince O2", [win['D'], terza_match2], key="res2")

        with b_cols[1]:
            st.success(f"🔥 QUARTO DI FINALE 1: {res1} vs {res2}")
            winner_final = st.selectbox("🏆 CAMPIONE DEL MONDO", [res1, res2, "..."], key="winner")

    with t_invio:
        st.button("INVIA PRONOSTICI", type="primary", use_container_width=True)
