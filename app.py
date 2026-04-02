import streamlit as st
import pandas as pd
import requests
import random
import json
import gspread
from io import StringIO
from google.oauth2.service_account import Credentials

# --- CONFIGURAZIONE ESTETICA ---
st.set_page_config(page_title="WC 2026 Contest", layout="wide")

# CSS Personalizzato per font e stile moderno
st.markdown("""
    <style>
    .main { background-color: #f9f9f9; }
    .match-card {
        background-color: white;
        border: 1px solid #e1e4e8;
        border-radius: 15px;
        padding: 15px;
        text-align: center;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.05);
        margin-bottom: 20px;
    }
    .team-name { font-size: 18px !important; font-weight: bold !important; color: #1e1e1e; }
    .points-info { font-size: 12px; color: #666; margin-top: 10px; }
    h1, h2, h3 { color: #0e1117; font-family: 'Trebuchet MS', sans-serif; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNZIONI TECNICHE ---
def get_flag(team_name):
    # Mapping veloce per le bandiere (ISO Codes)
    mapping = {
        "Messico": "mx", "Sudafrica": "za", "Corea Sud": "kr", "Rep. Ceca": "cz",
        "Canada": "ca", "Bosnia": "ba", "Qatar": "qa", "Svizzera": "ch",
        "Brasile": "br", "Marocco": "ma", "Haiti": "ht", "Scozia": "gb-sct",
        "USA": "us", "Paraguay": "py", "Australia": "au", "Turchia": "tr",
        "Germania": "de", "Curaçao": "cw", "Costa d'Avorio": "ci", "Ecuador": "ec",
        "Olanda": "nl", "Giappone": "jp", "Svezia": "se", "Tunisia": "tn",
        "Belgio": "be", "Egitto": "eg", "Iran": "ir", "Nuova Zelanda": "nz",
        "Spagna": "es", "Capo Verde": "cv", "Arabia Saudita": "sa", "Uruguay": "uy",
        "Francia": "fr", "Senegal": "sn", "Iraq": "iq", "Norvegia": "no",
        "Argentina": "ar", "Algeria": "dz", "Austria": "at", "Giordania": "jo",
        "Portogallo": "pt", "RD Congo": "cd", "Uzbekistan": "uz", "Colombia": "co",
        "Inghilterra": "gb-eng", "Croazia": "hr", "Ghana": "gh", "Panama": "pa"
    }
    code = mapping.get(team_name, "un")
    return f"https://flagcdn.com/w80/{code}.png"

@st.cache_data
def carica_partite():
    # Caricamento backup (già ottimizzato per velocità)
    nomi_gironi = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L']
    backup_teams = [
        ["Messico", "Sudafrica", "Corea Sud", "Rep. Ceca"], ["Canada", "Bosnia", "Qatar", "Svizzera"], 
        ["Brasile", "Marocco", "Haiti", "Scozia"], ["USA", "Paraguay", "Australia", "Turchia"], 
        ["Germania", "Curaçao", "Costa d'Avorio", "Ecuador"], ["Olanda", "Giappone", "Svezia", "Tunisia"], 
        ["Belgio", "Egitto", "Iran", "Nuova Zelanda"], ["Spagna", "Capo Verde", "Arabia Saudita", "Uruguay"], 
        ["Francia", "Senegal", "Iraq", "Norvegia"], ["Argentina", "Algeria", "Austria", "Giordania"], 
        ["Portogallo", "RD Congo", "Uzbekistan", "Colombia"], ["Inghilterra", "Croazia", "Ghana", "Panama"]
    ]
    final_matches = []
    for i, sq in enumerate(backup_teams):
        for idx1, idx2 in [(0,1), (2,3), (0,2), (1,3), (0,3), (1,2)]:
            final_matches.append({"gr": nomi_gironi[i], "h": sq[idx1], "a": sq[idx2], "hr": random.randint(15,45), "ar": random.randint(15,45)})
    return final_matches

def connetti_gsheet():
    info_chiave = json.loads(st.secrets["service_account"])
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(info_chiave, scopes=scope)
    client = gspread.authorize(creds)
    return client.open_by_url("https://docs.google.com/spreadsheets/d/1palUSBw4IlBFzU4dKtgT0tnjPiPEtxIc6K-DK05vXG8/edit?gid=0#gid=0").sheet1

# --- LOGICA APP ---
partite = carica_partite()
PASSWORD_ADMIN = "mondiali2026"

# Sidebar Admin
st.sidebar.image("https://upload.wikimedia.org/wikipedia/it/e/e0/Generic_Football_Logo.png", width=100)
admin_pass = st.sidebar.text_input("Admin Password", type="password")
admin_mode = (admin_pass == PASSWORD_ADMIN)

if admin_mode:
    st.title("👑 Pannello Admin")
    st.write("Gestisci i risultati reali e la classifica qui.")
    # (Inseriremo qui la logica classifica)
else:
    st.title("🏆 FIFA World Cup 2026 Contest")
    nickname = st.text_input("✨ Inizia inserendo il tuo Nickname per sbloccare il gioco:", placeholder="Esempio: Bomber99")

    if not nickname:
        st.warning("Per favore, inserisci il tuo nickname per visualizzare le partite e partecipare!")
    else:
        st.success(f"Benvenuto {nickname}! Compila i tuoi pronostici qui sotto.")
        
        tab1, tab2, tab3 = st.tabs(["🌍 Fase a Gironi", "⚔️ Eliminazione Diretta", "🚀 Invia"])

        with tab1:
            # TASTO AUTO-FILL (Solo per te in fase di test)
            if st.button("🎲 Test: Compila a Caso"):
                for i in range(72):
                    st.session_state[f"h_{i}"] = random.randint(0, 3)
                    st.session_state[f"a_{i}"] = random.randint(0, 3)
                st.rerun()

            # GRIGLIA 4 COLONNE
            cols = st.columns(4)
            for i, p in enumerate(partite):
                with cols[i % 4]:
                    st.markdown(f"""
                    <div class="match-card">
                        <div style="display: flex; justify-content: space-around; align-items: center;">
                            <div><img src="{get_flag(p['h'])}" width="40"><br><span class="team-name">{p['h']}</span></div>
                            <div style="font-size: 20px; font-weight: bold;">VS</div>
                            <div><img src="{get_flag(p['a'])}" width="40"><br><span class="team-name">{p['a']}</span></div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Input compatti
                    c_in1, c_in2 = st.columns(2)
                    with c_in1:
                        val_h = st.number_input("H", 0, 9, key=f"h_{i}", label_visibility="collapsed")
                    with c_in2:
                        val_a = st.number_input("A", 0, 9, key=f"a_{i}", label_visibility="collapsed")
                    
                    punti_x = (p['hr'] + p['ar']) // 2
                    st.markdown(f"<div class='points-info'><b>Gr.{p['gr']}</b> | 1: {p['hr']} - X: {punti_x} - 2: {p['ar']}</div>", unsafe_allow_html=True)
                    st.write("---")

        with tab2:
            st.header("🏆 Il tuo Bracket")
            st.write("Qui si genererà il tabellone basato sui tuoi risultati.")

        with tab3:
            st.header("🚀 Invia i Pronostici")
            if st.button("SALVA DEFINITIVAMENTE", type="primary"):
                try:
                    # Logica di salvataggio (Nickname + Risultati)
                    # foglio = connetti_gsheet() ...
                    st.success("Pronostici salvati! Buona fortuna!")
                    st.balloons()
                except:
                    st.error("Errore di connessione al database.")
