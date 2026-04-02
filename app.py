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
    url_foglio = "INCOLLA_QUI_IL_TUO_URL_DI_GOOGLE_SHEETS"
    return client.open_by_url(url_foglio)

# --- 2. CARICAMENTO PARTITE (WIKIPEDIA) ---
@st.cache_data
def carica_partite():
    url_wiki = "https://en.wikipedia.org/wiki/2026_FIFA_World_Cup"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        risposta = requests.get(url_wiki, headers=headers)
        tabelle = pd.read_html(StringIO(risposta.text))
        nomi_gironi = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L']
        gruppi = []
        for tab in tabelle:
            if len(tab) == 4 and any('team' in str(c).lower() for c in tab.columns):
                col = [c for c in tab.columns if 'team' in str(c).lower()][0]
                gruppi.append(tab[col].astype(str).apply(lambda x: x.split(' (')[0].strip()).tolist())
                if len(gruppi) == 12: break
        
        final_matches = []
        for i, sq in enumerate(gruppi):
            for idx1, idx2 in [(0,1), (2,3), (0,2), (1,3), (0,3), (1,2)]:
                final_matches.append({"gr": nomi_gironi[i], "h": sq[idx1], "a": sq[idx2], "hr": random.randint(10,50), "ar": random.randint(10,50)})
        return final_matches
    except:
        return [] # Ritorna vuoto se Wikipedia blocca

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
    if not partite:
        st.error("Errore nel caricamento delle partite. Riprova più tardi.")
    else:
        # Mostriamo le 72 partite raggruppate
        for p in partite:
            c1, c2, c3, c4, c5 = st.columns([3, 2, 1, 2, 3])
            with c1: st.write(f"**{p['h']}**")
            with c2: 
                res_h = st.number_input("", min_value=0, max_value=9, key=f"h_{p['h']}_{p['a']}", label_visibility="collapsed")
            with c3: st.write("-")
            with c4: 
                res_a = st.number_input("", min_value=0, max_value=9, key=f"a_{p['h']}_{p['a']}", label_visibility="collapsed")
            with c5: st.write(f"**{p['a']}**")
            # Salviamo il risultato nello stato dell'app
            st.session_state.pronostici[f"{p['h']}-{p['a']}"] = f"{res_h}-{res_a}"
            st.caption(f"Girone {p['gr']} | 1: {p['hr']}pt | X: {(p['hr']+p['ar'])//2}pt | 2: {p['ar']}pt")
            st.divider()

with tab2:
    st.header("Fase Finale")
    st.info("Qui potrai completare il tabellone una volta inseriti i gironi.")
    if st.button("Genera Bracket"):
        st.success("Tabellone generato con successo (Logica in attivazione)!")

with tab3:
    st.header("Conferma e Invia")
    if st.button("SALVA PRONOSTICI", type="primary"):
        if not nickname:
            st.error("Inserisci un nickname!")
        else:
            try:
                db = connetti_gsheet()
                foglio_utenti = db.sheet1
                # Salviamo Nome + Tutti i pronostici in formato JSON stringa
                dati = [nickname, json.dumps(st.session_state.pronostici)]
                foglio_utenti.append_row(dati)
                st.success("Dati salvati! Buona fortuna!")
                st.balloons()
            except Exception as e:
                st.error(f"Errore: {e}")
