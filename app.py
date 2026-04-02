import streamlit as st
import pandas as pd
import requests
import random
import json
import gspread
from io import StringIO
from google.oauth2.service_account import Credentials

# --- 1. CONNESSIONE DATABASE ---
def connetti_gsheet():
    info_chiave = json.loads(st.secrets["service_account"])
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(info_chiave, scopes=scope)
    client = gspread.authorize(creds)
    # !!! INCOLLA IL TUO URL QUI SOTTO !!!
    url_foglio = "https://docs.google.com/spreadsheets/d/1palUSBw4IlBFzU4dKtgT0tnjPiPEtxIc6K-DK05vXG8/edit?gid=0#gid=0"
    return client.open_by_url(url_foglio)

# --- 2. CARICAMENTO PARTITE (CON BACKUP AUTOMATICO) ---
@st.cache_data
def carica_partite():
    url_wiki = "https://en.wikipedia.org/wiki/2026_FIFA_World_Cup"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    nomi_gironi = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L']
    gruppi = []
    
    try:
        risposta = requests.get(url_wiki, headers=headers, timeout=10)
        tabelle = pd.read_html(StringIO(risposta.text))
        for tab in tabelle:
            if len(tab) == 4 and any('team' in str(c).lower() for c in tab.columns):
                col = [c for c in tab.columns if 'team' in str(c).lower()][0]
                gruppi.append(tab[col].astype(str).apply(lambda x: x.split(' (')[0].strip()).tolist())
                if len(gruppi) == 12: break
    except:
        pass # Se fallisce, gruppi resterà vuoto o incompleto e scatterà il backup sotto

    # SE WIKIPEDIA FALLISCE, USIAMO QUESTI DATI REALI (BACKUP)
    if len(gruppi) < 12:
        gruppi = [
            ["Messico", "Sudafrica", "Corea Sud", "Rep. Ceca"], ["Canada", "Bosnia", "Qatar", "Svizzera"], 
            ["Brasile", "Marocco", "Haiti", "Scozia"], ["USA", "Paraguay", "Australia", "Turchia"], 
            ["Germania", "Curaçao", "Costa d'Avorio", "Ecuador"], ["Olanda", "Giappone", "Svezia", "Tunisia"], 
            ["Belgio", "Egitto", "Iran", "Nuova Zelanda"], ["Spagna", "Capo Verde", "Arabia Saudita", "Uruguay"], 
            ["Francia", "Senegal", "Iraq", "Norvegia"], ["Argentina", "Algeria", "Austria", "Giordania"], 
            ["Portogallo", "RD Congo", "Uzbekistan", "Colombia"], ["Inghilterra", "Croazia", "Ghana", "Panama"]
        ]
    
    final_matches = []
    for i, sq in enumerate(gruppi):
        for idx1, idx2 in [(0,1), (2,3), (0,2), (1,3), (0,3), (1,2)]:
            final_matches.append({
                "gr": nomi_gironi[i], 
                "h": sq[idx1], 
                "a": sq[idx2], 
                "hr": random.randint(15,45), 
                "ar": random.randint(15,45)
            })
    return final_matches

# --- 3. CONFIGURAZIONE ---
st.set_page_config(page_title="Mondiali 2026 Contest", layout="centered")
partite = carica_partite()

if 'pronostici' not in st.session_state:
    st.session_state.pronostici = {}

# --- 4. INTERFACCIA ---
st.title("🏆 FIFA World Cup 2026 Contest")
nickname = st.text_input("Inserisci il tuo Nickname:")

tab1, tab2, tab3 = st.tabs(["🌍 Gironi", "⚔️ Tabellone", "🚀 Invia"])

with tab1:
    st.header("Fase a Gironi")
    # Mostriamo le 72 partite
    for i, p in enumerate(partite):
        with st.container():
            c1, c2, c3, c4, c5 = st.columns([3, 1, 0.5, 1, 3])
            with c1: st.write(f"**{p['h']}**")
            with c2: 
                res_h = st.number_input("G Casa", min_value=0, max_value=9, key=f"h_{i}", label_visibility="collapsed")
            with c3: st.write("-")
            with c4: 
                res_a = st.number_input("G Trasf", min_value=0, max_value=9, key=f"a_{i}", label_visibility="collapsed")
            with c5: st.write(f"**{p['a']}**")
            
            punti_x = (p['hr'] + p['ar']) // 2
            st.caption(f"Gr.{p['gr']} | Punti: 1(**{p['hr']}**) - X(**{punti_x}**) - 2(**{p['ar']}**)")
            st.session_state.pronostici[f"{p['h']}-{p['a']}"] = f"{res_h}-{res_a}"
            st.divider()

with tab2:
    st.header("Fase Finale")
    st.info("Compila i gironi e clicca per generare il tuo Bracket.")
    if st.button("Genera Bracket"):
        st.success("Tabellone generato (Matematica in corso...)")

with tab3:
    st.header("Conferma e Invia")
    if st.button("SALVA DEFINITIVAMENTE", type="primary"):
        if not nickname:
            st.error("Inserisci un nickname!")
        else:
            try:
                db = connetti_gsheet()
                foglio = db.sheet1
                # Salviamo Nickname + Pronostici
                dati = [nickname, json.dumps(st.session_state.pronostici)]
                foglio.append_row(dati)
                st.success(f"Dati inviati! Buona fortuna {nickname}!")
                st.balloons()
            except Exception as e:
                st.error(f"Errore di connessione al database: {e}")
