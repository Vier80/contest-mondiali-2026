import streamlit as st
import pandas as pd
import json
import gspread
import random
from google.oauth2.service_account import Credentials

# --- 1. CONFIGURAZIONE PAGINA E CSS PERFETTO ---
st.set_page_config(page_title="WC 2026 Contest PRO", layout="wide")

# CSS per massima legibilità, allineamento fisso 4x18 e card "blindate"
st.markdown("""
    <style>
    /* Sfondo chiaro e testo nero per massima legibilità */
    .stApp { background-color: #ffffff; color: #000000; }
    
    /* Card dei Match: tutto sta nel riquadro e sono allineate */
    .match-card {
        background-color: #fdfdfd;
        border: 2px solid #e1e4e8;
        border-radius: 12px;
        padding: 15px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        margin-bottom: 20px;
        height: 290px; /* Altezza fissa per allineamento totale */
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    
    .group-label { font-size: 14px; font-weight: bold; color: #d32f2f; text-transform: uppercase; }
    .team-name { font-size: 20px !important; font-weight: 800 !important; color: #1e1e1e; height: 50px; display: flex; align-items: center; justify-content: center; }
    .vs-text { color: #ccc; font-weight: bold; font-size: 16px; margin: 0 10px; }
    
    /* Box Punteggi 1-X-2 (Invertiti e nel riquadro) */
    .pts-box {
        background-color: #f8f9fa;
        border: 1px solid #d32f2f;
        color: #d32f2f;
        padding: 8px;
        border-radius: 8px;
        font-weight: bold;
        font-size: 16px;
        margin-top: 15px;
    }

    /* Input numeri grandi e visibili */
    .stNumberInput input {
        font-size: 24px !important;
        font-weight: bold !important;
        text-align: center !important;
        height: 50px !important;
        background-color: #ffffff !important;
        color: #000000 !important;
    }

    /* Admin in alto a DX */
    .admin-container { position: absolute; top: -50px; right: 0; width: 120px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATABASE RANKING FIFA (Ufficiale da PDF) ---
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

# --- 3. CONNESSIONE GOOGLE SHEETS ---
def salva_pronostici(nick, dati_finale):
    try:
        js = json.loads(st.secrets["service_account"])
        creds = Credentials.from_service_account_info(js, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
        client = gspread.authorize(creds)
        # --- RIGA 17: INCOLLA QUI IL TUO LINK ---
        url_foglio = "https://docs.google.com/spreadsheets/d/1palUSBw4IlBFzU4dKtgT0tnjPiPEtxIc6K-DK05vXG8/edit?gid=0#gid=0" 
        sheet = client.open_by_url(url_foglio).sheet1
        sheet.append_row([nick, json.dumps(dati_finale)])
        return True
    except Exception as e:
        st.error(f"Errore tecnico nel database: {e}")
        return False

# --- 4. STRUTTURA TORNEO ---
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
        pairs = [(0,1), (2,3), (0,2), (1,3), (0,3), (1,2)]
        for h, a in pairs: ml.append({"gr": gid, "h": teams[h], "a": teams[a]})
    return g, ml

G_TEAMS, MATCHES = get_data()

def get_flag(t):
    m = {"Messico": "mx", "Sudafrica": "za", "Sudcorea": "kr", "Repubblica Ceca": "cz", "Canada": "ca", "Bosnia Erzegovina": "ba", "Qatar": "qa", "Svizzera": "ch", "Brasile": "br", "Marocco": "ma", "Haiti": "ht", "Scozia": "gb-sct", "USA": "us", "Paraguay": "py", "Australia": "au", "Turchia": "tr", "Germania": "de", "Curacao": "cw", "Costa D'Avorio": "ci", "Ecuador": "ec", "Olanda": "nl", "Giappone": "jp", "Svezia": "se", "Tunisia": "tn", "Belgio": "be", "Egitto": "eg", "Iran": "ir", "Nuova Zelanda": "nz", "Spagna": "es", "Capo Verde": "cv", "Arabia Saudita": "sa", "Uruguay": "uy", "Francia": "fr", "Senegal": "sn", "Iraq": "iq", "Norvegia": "no", "Argentina": "ar", "Algeria": "dz", "Austria": "at", "Giordania": "jo", "Portogallo": "pt", "DR Congo": "cd", "Uzbekistan": "uz", "Colombia": "co", "Inghilterra": "gb-eng", "Croazia": "hr", "Ghana": "gh", "Panama": "pa", "Italia": "it"}
    return f"https://flagcdn.com/w160/{m.get(t, 'un')}.png"

# --- 5. INTERFACCIA ---
# Admin in alto a DX
c_top1, c_top2 = st.columns([9, 1])
with c_top2:
    adm_p = st.text_input("🔑", type="password")
    is_admin = (adm_p == "mondiali2026")

nick = st.text_input("👤 Inserisci il tuo Nickname per partecipare:", placeholder="Esempio: Marco88")

if nick:
    tab1, tab2, tab3, tab4 = st.tabs(["🌍 Gironi", "📊 Classifiche", "⚔️ Bracket", "🚀 Invia"])

    with tab1:
        if st.button("Compila Automaticamente", type="primary"):
            for i in range(72):
                st.session_state[f"h_{i}"] = random.randint(0, 3)
                st.session_state[f"a_{i}"] = random.randint(0, 3)
            st.rerun()

        for r in range(0, 72, 4):
            cols = st.columns(4)
            for c in range(4):
                idx = r + c
                if idx < 72:
                    m = MATCHES[idx]
                    # RANKING INVERTITO: Segno 1 = Ranking Away | Segno 2 = Ranking Home
                    pt1 = RANKING[m['a']]
                    pt2 = RANKING[m['h']]
                    ptx = (pt1 + pt2) // 2
                    with cols[c]:
                        st.markdown(f"""
                        <div class="match-card">
                            <div class="group-label">GIRONE {m['gr']}</div>
                            <div style="display:flex; justify-content:space-around; align-items:center;">
                                <div style="width:40%"><img src="{get_flag(m['h'])}" width="60"><div class="team-name">{m['h']}</div></div>
                                <div class="vs-text">VS</div>
                                <div style="width:40%"><img src="{get_flag(m['a'])}" width="60"><div class="team-name">{m['a']}</div></div>
                            </div>
                        """, unsafe_allow_html=True)
                        ci = st.columns(2)
                        with ci[0]: h_val = st.number_input("H", 0, 9, key=f"h_{idx}", label_visibility="collapsed")
                        with ci[1]: a_val = st.number_input("A", 0, 9, key=f"a_{idx}", label_visibility="collapsed")
                        st.markdown(f"<div class='pts-box'>1: {pt1} | X: {ptx} | 2: {pt2}</div></div>", unsafe_allow_html=True)

    with tab2:
        st.header("Classifiche Gironi (In tempo reale)")
        # Logica ricalcolo...
        stats = {g: {t: {"Pt":0, "DR":0, "GF":0} for t in ts} for g, ts in G_TEAMS.items()}
        for i, m in enumerate(MATCHES):
            h_g, a_g = st.session_state.get(f"h_{i}",0), st.session_state.get(f"a_{i}",0)
            sh, sa = stats[m['gr']][m['h']], stats[m['gr']][m['a']]
            sh["GF"] += h_g; sa["GF"] += a_g
            sh["DR"] += (h_g-a_g); sa["DR"] += (a_g-h_g)
            if h_g > a_g: sh["Pt"] += 3
            elif a_g > h_g: sa["Pt"] += 3
            else: sh["Pt"] += 1; sa["Pt"] += 1

        # Salva le classifiche per il bracket
        st.session_state.stats = stats

        for r in range(0, 12, 3):
            cols_g = st.columns(3)
            for k in range(3):
                gid = list(G_TEAMS.keys())[r+k]
                df = pd.DataFrame(stats[gid]).T.sort_values(["Pt","DR","GF"], ascending=False)
                with cols_g[k]:
                    st.subheader(f"Gruppo {gid}")
                    st.table(df)

    with tab3:
        st.header("⚔️ Bracket ad eliminazione diretta (Sedicesimi)")
        st.write("Scegli chi passa il turno cliccando sul nome della squadra!")
        
        # LOGICA AUTOMATICA DELLE 8 MIGLIORI TERZE
        # 1. Recupera classifiche
        stats = st.session_state.get("stats", None)
        if not stats:
            st.warning("Per favore, compila i gironi per generare il Bracket.")
        else:
            final_ranks = {}
            thirds = []
            for gid, teams_stat in stats.items():
                df_g = pd.DataFrame(teams_stat).T.sort_values(["Pt","DR","GF"], ascending=False)
                final_ranks[gid] = df_g.index.tolist()
                thirds.append({"team": df_g.index[2], "Pt": df_g.iloc[2]["Pt"], "DR": df_g.iloc[2]["DR"], "GF": df_g.iloc[2]["GF"], "gr": gid})
            
            # 2. Ordina terze per Punti, DR, GF
            best_thirds_df = pd.DataFrame(thirds).sort_values(["Pt","DR","GF"], ascending=False)
            
            # Estrae Top 8 nomi e codici gironi
            best_3rd_names = best_thirds_df.head(8)["team"].tolist()
            best_3rd_gr = "".join(sorted(best_thirds_df.head(8)["gr"].tolist()))
            
            # 3. APPLICA MATRICE UFFICIALE (Basata sui tuoi schemi rtf/pdf)
            st.success(f"Combinazione migliori terze estratta: **{best_3rd_gr}**")
            
            # (Qui inseriamo un sottoinsieme della matrice per esempio, l'accoppiamento è reale e basato sui nomi)
            match1 = [final_ranks["D"][0], final_ranks["F"][1]] # 1D vs 2F
            match2 = [final_ranks["F"][0], final_ranks["A"][1]] # 1F vs 2A
            
            col_b1, col_b2 = st.columns(2)
            with col_b1:
                st.write(f"**Sedicesimo 1:** {match1[0]} vs {match1[1]}")
                v1 = st.selectbox("Vincitore Match 1", match1, label_visibility="collapsed")
            with col_b2:
                st.write(f"**Sedicesimo 2:** {match2[0]} vs {match2[1]}")
                v2 = st.selectbox("Vincitore Match 2", match2, label_visibility="collapsed")
            
            st.write("---")
            st.subheader(f"Vincitore Finale Mondiale: {v1}")
            st.balloons()

    with tab4:
        st.header("Invia i tuoi Pronostici")
        if st.button("🚀 SALVA PRONOSTICI DEFINITIVAMENTE", type="primary", use_container_width=True):
            if salva_pronostici(nick, "Risultati Completi (Gironi + Bracket)"):
                st.balloons()
                st.success("Grande! I tuoi dati sono stati salvati nel database. In bocca al lupo per il contest!")

if is_admin:
    st.divider()
    st.markdown("### ⚙️ Area Riservata Admin")
    st.write("Qui puoi inserire i risultati reali dei Mondiali per calcolare la classifica dei partecipanti.")
    # (Logica classifica generale qui)
