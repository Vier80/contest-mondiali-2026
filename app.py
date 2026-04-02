import streamlit as st
import pandas as pd
import json
import gspread
import random
from google.oauth2.service_account import Credentials

# --- 1. CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="WC 2026 Contest PRO", layout="wide")

# CSS: Stilizzazione Card e Layout
st.markdown("""
<style>
.stApp { background-color: #f5f5f5; color: #111; }
[data-testid="column"] { padding: 0 5px !important; }
[data-testid="column"] > div {
    background: #ffffff;
    border: 2px solid #e1e4e8;
    border-radius: 12px;
    padding: 10px 8px 12px 8px !important;
    box-shadow: 0 3px 8px rgba(0,0,0,0.06);
    margin-bottom: 14px;
}
input[type="number"] {
    font-size: 22px !important;
    font-weight: 900 !important;
    text-align: center !important;
    height: 46px !important;
    border-radius: 8px !important;
    border: 2px solid #e1e4e8 !important;
    background: #f8f9fa !important;
    color: #111 !important;
}
.stNumberInput label { display: none !important; }
[data-testid="stImage"] { display: flex !important; justify-content: center !important; margin: 0 auto !important; }
[data-testid="stImage"] img { border-radius: 3px !important; box-shadow: 0 1px 4px rgba(0,0,0,0.18) !important; }
[data-testid="column"] p { text-align: center !important; }
</style>
""", unsafe_allow_html=True)

# --- 2. DATABASE RANKING E GRUPPI ---
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

# --- 3. CONNESSIONE GOOGLE SHEETS ---
def salva_pronostici(nick, dati_completi):
    try:
        # Recupera le credenziali dai secrets di Streamlit
        js = json.loads(st.secrets["service_account"])
        creds = Credentials.from_service_account_info(
            js,
            scopes=["https://www.googleapis.com/auth/spreadsheets",
                    "https://www.googleapis.com/auth/drive"]
        )
        client = gspread.authorize(creds)
        
        # --- INSERISCI QUI IL TUO LINK ---
        URL_FOGLIO = "https://docs.google.com/spreadsheets/d/1palUSBw4IlBFzU4dKtgT0tnjPiPEtxIc6K-DK05vXG8/edit?gid=0#gid=0" 
        
        sheet = client.open_by_url(URL_FOGLIO).sheet1
        sheet.append_row([nick, json.dumps(dati_completi)])
        return True
    except Exception as e:
        st.error(f"Errore durante il salvataggio: {e}")
        return False

# --- 4. LOGICA CALCOLO CLASSIFICHE ---
def calcola_classifiche():
    # Inizializza statistiche
    stats = {g: {t: {"Pt": 0, "DR": 0, "GF": 0} for t in ts} for g, ts in G_TEAMS.items()}
    
    # Elabora risultati gironi
    for i, m in enumerate(MATCHES):
        h_g = st.session_state.get(f"h_{i}", 0)
        a_g = st.session_state.get(f"a_{i}", 0)
        sh, sa = stats[m['gr']][m['h']], stats[m['gr']][m['a']]
        sh["GF"] += h_g; sa["GF"] += a_g
        sh["DR"] += (h_g - a_g); sa["DR"] += (a_g - h_g)
        if h_g > a_g: sh["Pt"] += 3
        elif a_g > h_g: sa["Pt"] += 3
        else: sh["Pt"] += 1; sa["Pt"] += 1
    
    final_ranks = {}
    thirds = []
    for gid, teams_stat in stats.items():
        # Ordinamento: Punti > DR > GF
        df_g = pd.DataFrame(teams_stat).T.sort_values(["Pt", "DR", "GF"], ascending=False)
        final_ranks[gid] = df_g.index.tolist()
        # Prendi la terza classificata di ogni girone
        thirds.append({
            "team": df_g.index[2], "Pt": df_g.iloc[2]["Pt"], 
            "DR": df_g.iloc[2]["DR"], "GF": df_g.iloc[2]["GF"], "gr": gid
        })
    
    # Seleziona le migliori 8 terze
    best_thirds = pd.DataFrame(thirds).sort_values(["Pt", "DR", "GF"], ascending=False).head(8)
    return final_ranks, best_thirds, stats

def get_third_opponent(slot, best_thirds_dict):
    """Assegna le terze ai vincitori dei gironi (Basato su RTF)"""
    disponibili = sorted(best_thirds_dict.keys())
    mapping = {
        "1D": disponibili[0] if len(disponibili) > 0 else "3D",
        "1B": disponibili[1] if len(disponibili) > 1 else "3B",
        "1A": disponibili[2] if len(disponibili) > 2 else "3A",
        "1C": disponibili[3] if len(disponibili) > 3 else "3C",
        "1G": disponibili[4] if len(disponibili) > 4 else "3G",
        "1I": disponibili[5] if len(disponibili) > 5 else "3I",
        "1K": disponibili[6] if len(disponibili) > 6 else "3K",
        "1L": disponibili[7] if len(disponibili) > 7 else "3L",
    }
    gr_trovato = mapping.get(slot)
    return best_thirds_dict.get(gr_trovato, f"3rd {slot[-1]}")

# --- 5. INTERFACCIA PRINCIPALE ---
nick = st.text_input("👤 Inserisci il tuo Nickname:", placeholder="Esempio: Bomber99")

if nick:
    tab1, tab2, tab3, tab4 = st.tabs(["🌍 Gironi", "📊 Classifiche", "⚔️ Bracket", "🚀 Invia"])

    # --- TAB 1: GIRONI ---
    with tab1:
        if st.button("Compila Random (Test)"):
            for i in range(72):
                st.session_state[f"h_{i}"] = random.randint(0, 4)
                st.session_state[f"a_{i}"] = random.randint(0, 4)
            st.rerun()

        for row in range(18):
            cols = st.columns(4)
            for c_idx in range(4):
                idx = row * 4 + c_idx
                if idx < 72:
                    m = MATCHES[idx]
                    with cols[c_idx]:
                        st.markdown(f"<p style='color:#d32f2f; font-size:10px; font-weight:800; margin-bottom:2px;'>⚽ GRP {m['gr']}</p>", unsafe_allow_html=True)
                        # Box Input
                        ci1, ci2 = st.columns(2)
                        st.session_state[f"h_{idx}"] = ci1.number_input(f"{m['h']}", 0, 9, key=f"in_h_{idx}", value=st.session_state.get(f"h_{idx}", 0))
                        st.session_state[f"a_{idx}"] = ci2.number_input(f"{m['a']}", 0, 9, key=f"in_a_{idx}", value=st.session_state.get(f"a_{idx}", 0))
                        st.markdown(f"<p style='font-size:11px; font-weight:600;'>{m['h']} - {m['a']}</p>", unsafe_allow_html=True)

    # --- TAB 2: CLASSIFICHE ---
    with tab2:
        final_ranks, best_thirds_df, stats = calcola_classifiche()
        st.header("Situazione Gironi")
        for i in range(0, 12, 3):
            cols = st.columns(3)
            for k in range(3):
                gid = list(G_TEAMS.keys())[i+k]
                df = pd.DataFrame(stats[gid]).T.sort_values(["Pt", "DR", "GF"], ascending=False)
                cols[k].subheader(f"Gruppo {gid}")
                cols[k].table(df)
        
        st.divider()
        st.subheader("Classifica Migliori Terze (Passano le prime 8)")
        st.table(best_thirds_df)

    # --- TAB 3: BRACKET ---
    with tab3:
        final_ranks, best_thirds_df, _ = calcola_classifiche()
        b_thirds = {row['gr']: row['team'] for _, row in best_thirds_df.iterrows()}
        
        st.header("⚔️ Sedicesimi di Finale (Round of 32)")
        st.write("Scegli chi passa il turno selezionando la squadra vincente.")

        # Definizione accoppiamenti (Basata su RTF e struttura 48 squadre)
        accoppiamenti = [
            ("M1", final_ranks["A"][1], final_ranks["C"][1]),
            ("M2", final_ranks["D"][0], get_third_opponent("1D", b_thirds)),
            ("M3", final_ranks["B"][0], get_third_opponent("1B", b_thirds)),
            ("M4", final_ranks["F"][0], final_ranks["E"][1]),
            ("M5", final_ranks["B"][1], final_ranks["F"][1]),
            ("M6", final_ranks["A"][0], get_third_opponent("1A", b_thirds)),
            ("M7", final_ranks["E"][0], final_ranks["D"][1]),
            ("M8", final_ranks["C"][0], get_third_opponent("1C", b_thirds)),
            ("M9", final_ranks["G"][0], final_ranks["I"][1]),
            ("M10", final_ranks["H"][0], final_ranks["J"][1]),
            ("M11", final_ranks["I"][0], get_third_opponent("1I", b_thirds)),
            ("M12", final_ranks["J"][0], final_ranks["L"][1]),
            ("M13", final_ranks["K"][0], get_third_opponent("1K", b_thirds)),
            ("M14", final_ranks["L"][0], final_ranks["G"][1]),
            ("M15", final_ranks["G"][1], final_ranks["H"][1]),
            ("M16", final_ranks["K"][1], get_third_opponent("1L", b_thirds))
        ]

        vincitori_s = {}
        cols_b = st.columns(4)
        for i, (m_id, t1, t2) in enumerate(accoppiamenti):
            with cols_b[i // 4]:
                st.markdown(f"**Match {i+1}**")
                choice = st.radio(f"Vince:", [t1, t2], key=f"br_{m_id}")
                vincitori_s[m_id] = choice
                st.divider()

        # Vincitore Finale (Semplificato per brevità)
        st.subheader("🏆 Vincitore Mondiale Pronosticato")
        campione = st.selectbox("Chi alzerà la coppa?", sorted(list(vincitori_s.values())))
        st.session_state["campione_finale"] = campione
        if campione:
            st.balloons()

    # --- TAB 4: INVIO ---
    with tab4:
        st.header("Salva i tuoi Pronostici")
        st.write("Controlla bene i tuoi dati prima di inviare. Una volta salvati non potrai più modificarli.")
        
        if st.button("🚀 INVIA PRONOSTICI DEFINITIVAMENTE", type="primary", use_container_width=True):
            # Prepara il pacchetto dati
            dati_da_salvare = {
                "Gironi": {f"Match_{i}": [st.session_state.get(f"h_{i}"), st.session_state.get(f"a_{i}")] for i in range(72)},
                "Campione": st.session_state.get("campione_finale", "Non selezionato")
            }
            
            if salva_pronostici(nick, dati_da_salvare):
                st.success(f"Grazie {nick}! I tuoi pronostici sono stati salvati correttamente.")
                st.confetti()
            else:
                st.error("C'è stato un problema col database. Controlla la configurazione dei Secrets o il link del foglio.")
