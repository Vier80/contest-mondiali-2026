import streamlit as st
import pandas as pd
import json
import gspread
import random
from google.oauth2.service_account import Credentials

# --- 1. CONFIGURAZIONE PAGINA E CSS PERFETTO ---
st.set_page_config(page_title="WC 2026 Contest PRO", layout="wide")

st.markdown("""
    <style>
    /* ============================
       RESET E BASE
    ============================ */
    .stApp { background-color: #f5f5f5; color: #000000; }

    /* Rimuovi padding extra delle colonne Streamlit */
    [data-testid="column"] {
        padding: 0 6px !important;
    }

    /* ============================
       CARD SUPERIORE (HTML)
       border-bottom: none + bordi inferiori piatti
       per "fondersi" con gli input sotto
    ============================ */
    .match-card-top {
        background-color: #ffffff;
        border: 2px solid #e1e4e8;
        border-bottom: none;              /* Si fonde con il blocco input */
        border-radius: 12px 12px 0 0;
        padding: 14px 12px 10px 12px;
        text-align: center;
        box-shadow: 0 2px 6px rgba(0,0,0,0.06);
        height: 210px;                    /* Altezza fissa per allineamento righe */
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: space-between;
        box-sizing: border-box;
    }

    .group-label {
        font-size: 11px;
        font-weight: 800;
        color: #d32f2f;
        text-transform: uppercase;
        letter-spacing: 1px;
        width: 100%;
        text-align: center;
    }

    /* Riga bandiere + VS */
    .teams-row {
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 6px;
        width: 100%;
        flex: 1;
        margin: 6px 0;
    }

    .team-block {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        width: 42%;
    }

    .team-block img {
        display: block;
        width: 52px;
        height: auto;
        margin: 0 auto 5px auto;
        border-radius: 3px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.15);
    }

    .team-name {
        font-size: 12px !important;
        font-weight: 800 !important;
        color: #1e1e1e;
        line-height: 1.2;
        text-align: center;
        min-height: 30px;
        display: flex;
        align-items: center;
        justify-content: center;
    }

    .vs-text {
        color: #ccc;
        font-weight: 900;
        font-size: 13px;
        flex-shrink: 0;
    }

    /* Box 1-X-2 in fondo alla card */
    .pts-box {
        background-color: #fff5f5;
        border: 1px solid #f5c6c6;
        color: #d32f2f;
        padding: 5px 8px;
        border-radius: 6px;
        font-weight: 700;
        font-size: 11px;
        width: 100%;
        text-align: center;
        box-sizing: border-box;
    }

    /* ============================
       BLOCCO INPUT (parte inferiore)
       border-top: none per fondersi con la card
    ============================ */
    [data-testid="column"] > div > div > div > div:has(.stNumberInput) {
        /* Non possiamo targettare direttamente, usiamo il wrapper sotto */
    }

    /* Wrapper che crea il bordo inferiore della card attorno agli input */
    .input-row-wrapper {
        background-color: #ffffff;
        border: 2px solid #e1e4e8;
        border-top: none;                 /* Si fonde con la card sopra */
        border-radius: 0 0 12px 12px;
        padding: 8px 12px 10px 12px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.06);
        display: flex;
        justify-content: space-around;
        align-items: center;
        gap: 8px;
        margin-bottom: 16px;
        box-sizing: border-box;
    }

    /* Label Casa / Ospite */
    .score-label {
        font-size: 10px;
        font-weight: 700;
        color: #888;
        text-transform: uppercase;
        text-align: center;
        margin-bottom: 2px;
    }

    /* Stile input numerici: grandi, centrati, integrati */
    .stNumberInput input {
        font-size: 22px !important;
        font-weight: 900 !important;
        text-align: center !important;
        height: 44px !important;
        background-color: #f8f9fa !important;
        color: #1e1e1e !important;
        border: 1px solid #d0d0d0 !important;
        border-radius: 8px !important;
    }

    .stNumberInput [data-testid="stNumberInputStepDown"],
    .stNumberInput [data-testid="stNumberInputStepUp"] {
        background-color: #f0f0f0 !important;
        border-color: #d0d0d0 !important;
    }

    /* Rimuovi margin top extra Streamlit sugli input */
    .stNumberInput { margin-top: 0 !important; margin-bottom: 0 !important; }
    div[data-testid="stVerticalBlock"] > div:has(.stNumberInput) {
        padding-top: 0 !important;
    }

    /* ============================
       DIVISORE TRA GIRONI
    ============================ */
    .group-divider {
        height: 2px;
        background: linear-gradient(to right, transparent, #d32f2f, transparent);
        margin: 6px 0 18px 0;
        border: none;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATABASE RANKING FIFA ---
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
        creds = Credentials.from_service_account_info(
            js,
            scopes=["https://www.googleapis.com/auth/spreadsheets",
                    "https://www.googleapis.com/auth/drive"]
        )
        client = gspread.authorize(creds)
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
        for h, a in pairs:
            ml.append({"gr": gid, "h": teams[h], "a": teams[a]})
    return g, ml

G_TEAMS, MATCHES = get_data()

def get_flag(t):
    m = {
        "Messico": "mx", "Sudafrica": "za", "Sudcorea": "kr",
        "Repubblica Ceca": "cz", "Canada": "ca", "Bosnia Erzegovina": "ba",
        "Qatar": "qa", "Svizzera": "ch", "Brasile": "br", "Marocco": "ma",
        "Haiti": "ht", "Scozia": "gb-sct", "USA": "us", "Paraguay": "py",
        "Australia": "au", "Turchia": "tr", "Germania": "de", "Curacao": "cw",
        "Costa D'Avorio": "ci", "Ecuador": "ec", "Olanda": "nl", "Giappone": "jp",
        "Svezia": "se", "Tunisia": "tn", "Belgio": "be", "Egitto": "eg",
        "Iran": "ir", "Nuova Zelanda": "nz", "Spagna": "es", "Capo Verde": "cv",
        "Arabia Saudita": "sa", "Uruguay": "uy", "Francia": "fr", "Senegal": "sn",
        "Iraq": "iq", "Norvegia": "no", "Argentina": "ar", "Algeria": "dz",
        "Austria": "at", "Giordania": "jo", "Portogallo": "pt", "DR Congo": "cd",
        "Uzbekistan": "uz", "Colombia": "co", "Inghilterra": "gb-eng",
        "Croazia": "hr", "Ghana": "gh", "Panama": "pa", "Italia": "it"
    }
    return f"https://flagcdn.com/w160/{m.get(t, 'un')}.png"

# --- 5. INTERFACCIA ---
c_top1, c_top2 = st.columns([9, 1])
with c_top2:
    adm_p = st.text_input("🔑", type="password")
    is_admin = (adm_p == "mondiali2026")

nick = st.text_input(
    "👤 Inserisci il tuo Nickname per partecipare:",
    placeholder="Esempio: Marco88"
)

if nick:
    tab1, tab2, tab3, tab4 = st.tabs(["🌍 Gironi", "📊 Classifiche", "⚔️ Bracket", "🚀 Invia"])

    # ============================================================
    #  TAB 1 – GIRONI: 4 card per riga × 18 righe = 72 partite
    # ============================================================
    with tab1:
        if st.button("Compila Automaticamente", type="primary"):
            for i in range(72):
                st.session_state[f"h_{i}"] = random.randint(0, 3)
                st.session_state[f"a_{i}"] = random.randint(0, 3)
            st.rerun()

        # Tiene traccia del girone precedente per inserire divisore
        prev_group = None

        for row in range(18):                   # 18 righe
            cols = st.columns(4, gap="small")   # 4 colonne con gap ridotto

            for col_idx in range(4):
                idx = row * 4 + col_idx         # indice partita 0-71

                m        = MATCHES[idx]
                pt_away  = RANKING[m['a']]      # Segno 1  = Ranking Away (come da logica originale)
                pt_home  = RANKING[m['h']]      # Segno 2  = Ranking Home
                pt_x     = (pt_away + pt_home) // 2
                flag_h   = get_flag(m['h'])
                flag_a   = get_flag(m['a'])

                with cols[col_idx]:
                    # ── Parte superiore: HTML centrato ──────────────────
                    st.markdown(f"""
                    <div class="match-card-top">

                        <div class="group-label">⚽ GIRONE {m['gr']}</div>

                        <div class="teams-row">
                            <div class="team-block">
                                <img src="{flag_h}" alt="{m['h']}">
                                <div class="team-name">{m['h']}</div>
                            </div>
                            <div class="vs-text">VS</div>
                            <div class="team-block">
                                <img src="{flag_a}" alt="{m['a']}">
                                <div class="team-name">{m['a']}</div>
                            </div>
                        </div>

                        <div class="pts-box">
                            🏠&nbsp;1:&nbsp;<b>{pt_away}</b>
                            &nbsp;|&nbsp;
                            ✖&nbsp;X:&nbsp;<b>{pt_x}</b>
                            &nbsp;|&nbsp;
                            ✈️&nbsp;2:&nbsp;<b>{pt_home}</b>
                        </div>

                    </div>
                    """, unsafe_allow_html=True)

                    # ── Parte inferiore: input numerici ─────────────────
                    # Wrapper HTML che "chiude" visivamente la card
                    st.markdown('<div class="input-row-wrapper">', unsafe_allow_html=True)

                    ci = st.columns(2)
                    with ci[0]:
                        st.markdown('<div class="score-label">🏠 Casa</div>', unsafe_allow_html=True)
                        st.number_input(
                            "Casa", min_value=0, max_value=9,
                            key=f"h_{idx}",
                            label_visibility="collapsed"
                        )
                    with ci[1]:
                        st.markdown('<div class="score-label">✈️ Ospite</div>', unsafe_allow_html=True)
                        st.number_input(
                            "Ospite", min_value=0, max_value=9,
                            key=f"a_{idx}",
                            label_visibility="collapsed"
                        )

                    st.markdown('</div>', unsafe_allow_html=True)

            # Divisore rosso tra gironi (ogni 6 partite = 1.5 righe → ogni volta che cambia girone)
            # Controlliamo il girone della prima partita della prossima riga
            if row < 17:
                curr_group = MATCHES[row * 4]["gr"]
                next_group = MATCHES[(row + 1) * 4]["gr"]
                if curr_group != next_group:
                    st.markdown('<hr class="group-divider">', unsafe_allow_html=True)

    # ============================================================
    #  TAB 2 – CLASSIFICHE
    # ============================================================
    with tab2:
        st.header("Classifiche Gironi (In tempo reale)")

        stats = {g: {t: {"Pt": 0, "DR": 0, "GF": 0} for t in ts}
                 for g, ts in G_TEAMS.items()}

        for i, m in enumerate(MATCHES):
            h_g = st.session_state.get(f"h_{i}", 0)
            a_g = st.session_state.get(f"a_{i}", 0)
            sh, sa = stats[m['gr']][m['h']], stats[m['gr']][m['a']]
            sh["GF"] += h_g;  sa["GF"] += a_g
            sh["DR"] += (h_g - a_g);  sa["DR"] += (a_g - h_g)
            if h_g > a_g:    sh["Pt"] += 3
            elif a_g > h_g:  sa["Pt"] += 3
            else:            sh["Pt"] += 1;  sa["Pt"] += 1

        st.session_state.stats = stats

        for r in range(0, 12, 3):
            cols_g = st.columns(3)
            for k in range(3):
                gid = list(G_TEAMS.keys())[r + k]
                df = pd.DataFrame(stats[gid]).T.sort_values(
                    ["Pt", "DR", "GF"], ascending=False
                )
                with cols_g[k]:
                    st.subheader(f"Gruppo {gid}")
                    st.table(df)

    # ============================================================
    #  TAB 3 – BRACKET
    # ============================================================
    with tab3:
        st.header("⚔️ Bracket ad eliminazione diretta (Sedicesimi)")
        st.write("Scegli chi passa il turno cliccando sul nome della squadra!")

        stats = st.session_state.get("stats", None)
        if not stats:
            st.warning("Per favore, compila i gironi per generare il Bracket.")
        else:
            final_ranks = {}
            thirds = []
            for gid, teams_stat in stats.items():
                df_g = pd.DataFrame(teams_stat).T.sort_values(
                    ["Pt", "DR", "GF"], ascending=False
                )
                final_ranks[gid] = df_g.index.tolist()
                thirds.append({
                    "team": df_g.index[2],
                    "Pt":   df_g.iloc[2]["Pt"],
                    "DR":   df_g.iloc[2]["DR"],
                    "GF":   df_g.iloc[2]["GF"],
                    "gr":   gid
                })

            best_thirds_df = pd.DataFrame(thirds).sort_values(
                ["Pt", "DR", "GF"], ascending=False
            )
            best_3rd_gr = "".join(sorted(best_thirds_df.head(8)["gr"].tolist()))

            st.success(f"Combinazione migliori terze estratta: **{best_3rd_gr}**")

            match1 = [final_ranks["D"][0], final_ranks["F"][1]]
            match2 = [final_ranks["F"][0], final_ranks["A"][1]]

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

    # ============================================================
    #  TAB 4 – INVIO
    # ============================================================
    with tab4:
        st.header("Invia i tuoi Pronostici")
        if st.button(
            "🚀 SALVA PRONOSTICI DEFINITIVAMENTE",
            type="primary",
            use_container_width=True
        ):
            if salva_pronostici(nick, "Risultati Completi (Gironi + Bracket)"):
                st.balloons()
                st.success(
                    "Grande! I tuoi dati sono stati salvati nel database. "
                    "In bocca al lupo per il contest!"
                )

# ============================================================
#  AREA ADMIN
# ============================================================
if is_admin:
    st.divider()
    st.markdown("### ⚙️ Area Riservata Admin")
    st.write(
        "Qui puoi inserire i risultati reali dei Mondiali "
        "per calcolare la classifica dei partecipanti."
    )
