import streamlit as st
import pandas as pd
import json
import gspread
import random
from google.oauth2.service_account import Credentials

# --- 1. CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="WC 2026 Contest PRO", layout="wide")

# CSS: stilizza SOLO elementi nativi Streamlit, zero HTML annidato
st.markdown("""
<style>
/* Sfondo e testo */
.stApp { background-color: #f5f5f5; color: #111; }

/* Riduci padding colonne */
[data-testid="column"] { padding: 0 5px !important; }

/* === CARD: bordo attorno al blocco colonna === */
[data-testid="column"] > div {
    background: #ffffff;
    border: 2px solid #e1e4e8;
    border-radius: 12px;
    padding: 10px 8px 12px 8px !important;
    box-shadow: 0 3px 8px rgba(0,0,0,0.06);
    margin-bottom: 14px;
}

/* Input numerici grandi e centrati */
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

/* Nascondi label degli input (usiamo label_visibility=collapsed) */
.stNumberInput label { display: none !important; }

/* Bottone step +/- */
.stNumberInput button {
    background: #f0f0f0 !important;
    border-radius: 6px !important;
}

/* Immagini bandiere sempre centrate */
[data-testid="stImage"] {
    display: flex !important;
    justify-content: center !important;
    margin: 0 auto !important;
}
[data-testid="stImage"] img {
    display: block !important;
    margin: 0 auto !important;
    border-radius: 3px !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.18) !important;
}

/* Testo centrato di default in tutta l'app */
[data-testid="column"] p { text-align: center !important; }
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
        pairs = [(0, 1), (2, 3), (0, 2), (1, 3), (0, 3), (1, 2)]
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

# ─────────────────────────────────────────────────────────────
# Helper: rendering di una singola card con SOLI componenti nativi
# ─────────────────────────────────────────────────────────────
def render_match_card(idx):
    """Renderizza una card partita usando solo st.image / st.markdown / st.number_input."""
    m      = MATCHES[idx]
    pt_a   = RANKING[m['a']]   # Segno 1  (ranking away)
    pt_h   = RANKING[m['h']]   # Segno 2  (ranking home)
    pt_x   = (pt_a + pt_h) // 2

    # ── Etichetta girone ──────────────────────────────────────
    st.markdown(
        f"<p style='text-align:center; color:#d32f2f; font-weight:800; "
        f"font-size:11px; letter-spacing:1px; margin-bottom:6px;'>"
        f"⚽ GIRONE {m['gr']}</p>",
        unsafe_allow_html=True
    )

    # ── Bandiere e nomi squadre su 3 colonne [2 - 1 - 2] ─────
    c1, c2, c3 = st.columns([2, 1, 2])

    with c1:
        st.image(get_flag(m['h']), width=56)
        st.markdown(
            f"<p style='font-size:12px; font-weight:800; color:#1e1e1e; "
            f"line-height:1.2; min-height:32px; display:flex; align-items:center; "
            f"justify-content:center;'>{m['h']}</p>",
            unsafe_allow_html=True
        )

    with c2:
        st.markdown(
            "<p style='font-size:15px; font-weight:900; color:#bbb; "
            "padding-top:12px;'>VS</p>",
            unsafe_allow_html=True
        )

    with c3:
        st.image(get_flag(m['a']), width=56)
        st.markdown(
            f"<p style='font-size:12px; font-weight:800; color:#1e1e1e; "
            f"line-height:1.2; min-height:32px; display:flex; align-items:center; "
            f"justify-content:center;'>{m['a']}</p>",
            unsafe_allow_html=True
        )

    # ── Box punteggi 1 | X | 2 ───────────────────────────────
    st.markdown(
        f"<p style='background:#fff5f5; border:1px solid #f5c6c6; color:#d32f2f; "
        f"border-radius:7px; font-size:11px; font-weight:700; padding:5px 4px; "
        f"margin:4px 0 6px 0;'>"
        f"🏠 1: <b>{pt_a}</b> &nbsp;|&nbsp; ✖ X: <b>{pt_x}</b> &nbsp;|&nbsp; ✈️ 2: <b>{pt_h}</b>"
        f"</p>",
        unsafe_allow_html=True
    )

    # ── Input risultato Home / Away ───────────────────────────
    ci1, ci2 = st.columns(2)
    with ci1:
        st.markdown(
            "<p style='font-size:10px; font-weight:700; color:#999; margin-bottom:1px;'>"
            "🏠 CASA</p>",
            unsafe_allow_html=True
        )
        st.number_input(
            "Casa", min_value=0, max_value=9,
            key=f"h_{idx}", label_visibility="collapsed"
        )
    with ci2:
        st.markdown(
            "<p style='font-size:10px; font-weight:700; color:#999; margin-bottom:1px;'>"
            "✈️ OSPITE</p>",
            unsafe_allow_html=True
        )
        st.number_input(
            "Ospite", min_value=0, max_value=9,
            key=f"a_{idx}", label_visibility="collapsed"
        )

# --- 5. INTERFACCIA PRINCIPALE ---
c_top1, c_top2 = st.columns([9, 1])
with c_top2:
    adm_p    = st.text_input("🔑", type="password")
    is_admin = (adm_p == "mondiali2026")

nick = st.text_input(
    "👤 Inserisci il tuo Nickname per partecipare:",
    placeholder="Esempio: Marco88"
)

if nick:
    tab1, tab2, tab3, tab4 = st.tabs(
        ["🌍 Gironi", "📊 Classifiche", "⚔️ Bracket", "🚀 Invia"]
    )

    # ────────────────────────────────────────────────────────
    #  TAB 1 – GIRONI  (4 card × 18 righe = 72 partite)
    # ────────────────────────────────────────────────────────
    with tab1:
        if st.button("Compila Automaticamente", type="primary"):
            for i in range(72):
                st.session_state[f"h_{i}"] = random.randint(0, 3)
                st.session_state[f"a_{i}"] = random.randint(0, 3)
            st.rerun()

        prev_group = None

        for row in range(18):                        # 18 righe
            cols = st.columns(4, gap="small")        # 4 colonne

            for col_idx in range(4):
                idx = row * 4 + col_idx              # partita 0-71
                with cols[col_idx]:
                    render_match_card(idx)

            # Divisore rosso tra gironi
            if row < 17:
                curr_gr = MATCHES[row * 4]["gr"]
                next_gr = MATCHES[(row + 1) * 4]["gr"]
                if curr_gr != next_gr:
                    st.markdown(
                        "<hr style='border:none; height:2px; "
                        "background:linear-gradient(to right,transparent,#d32f2f,transparent); "
                        "margin:4px 0 16px 0;'>",
                        unsafe_allow_html=True
                    )

    # ────────────────────────────────────────────────────────
    #  TAB 2 – CLASSIFICHE
    # ────────────────────────────────────────────────────────
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
            if   h_g > a_g: sh["Pt"] += 3
            elif a_g > h_g: sa["Pt"] += 3
            else:            sh["Pt"] += 1; sa["Pt"] += 1

        st.session_state.stats = stats

        for r in range(0, 12, 3):
            cols_g = st.columns(3)
            for k in range(3):
                gid = list(G_TEAMS.keys())[r + k]
                df  = pd.DataFrame(stats[gid]).T.sort_values(
                    ["Pt", "DR", "GF"], ascending=False
                )
                with cols_g[k]:
                    st.subheader(f"Gruppo {gid}")
                    st.table(df)

    # ────────────────────────────────────────────────────────
    #  TAB 3 – BRACKET
    # ────────────────────────────────────────────────────────
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
                    "Pt": df_g.iloc[2]["Pt"],
                    "DR": df_g.iloc[2]["DR"],
                    "GF": df_g.iloc[2]["GF"],
                    "gr": gid
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

            st.divider()
            st.subheader(f"🏆 Vincitore Finale Mondiale: {v1}")
            st.balloons()

    # ────────────────────────────────────────────────────────
    #  TAB 4 – INVIO
    # ────────────────────────────────────────────────────────
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

# ────────────────────────────────────────────────────────
#  AREA ADMIN
# ────────────────────────────────────────────────────────
if is_admin:
    st.divider()
    st.markdown("### ⚙️ Area Riservata Admin")
    st.write(
        "Qui puoi inserire i risultati reali dei Mondiali "
        "per calcolare la classifica dei partecipanti."
    )
