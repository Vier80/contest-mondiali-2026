import streamlit as st
import pandas as pd
import json
import gspread
from google.oauth2.service_account import Credentials

# --- 1. FUNZIONE SEGRETA PER IL DATABASE ---
# Questa funzione apre la "scatola" che hai incollato nei Secrets di Streamlit
def connetti_gsheet():
    # Carica i dati dal segreto 'service_account' (quello con gli apici ''')
    info_chiave = json.loads(st.secrets["service_account"])
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(info_chiave, scopes=scope)
    client = gspread.authorize(creds)
    
    # !!! ATTENZIONE: Incolla qui sotto l'URL del tuo Google Sheet !!!
    url_foglio = "https://docs.google.com/spreadsheets/d/1palUSBw4IlBFzU4dKtgT0tnjPiPEtxIc6K-DK05vXG8/edit?gid=0#gid=0"
    return client.open_by_url(url_foglio).sheet1

# --- 2. CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Contest Mondiali 2026", page_icon="🏆", layout="centered")
PASSWORD_ADMIN = "mondiali2026"

# --- 3. SIDEBAR & ADMIN ---
st.sidebar.title("👑 Area Admin")
admin_pass = st.sidebar.text_input("Password", type="password")
admin_mode = True if admin_pass == PASSWORD_ADMIN else False

# --- 4. INTERFACCIA UTENTE ---
if not admin_mode:
    st.title("🏆 Contest Mondiali 2026")
    giocatore = st.text_input("Il tuo Nome o Nickname:")
    
    tab1, tab2, tab3 = st.tabs(["🌍 Gironi", "⚔️ Tabellone", "🚀 Invia"])
    
    with tab1:
        st.info("Qui i tuoi amici inseriranno i risultati dei 72 match.")
        # Nota: Qui poi integreremo la lista automatica da Wikipedia che abbiamo testato
        
    with tab2:
        st.info("Qui comparirà il tabellone a cascata.")

    with tab3:
        st.header("Invia i tuoi Pronostici")
        if st.button("SALVA DEFINITIVAMENTE", type="primary"):
            if not giocatore:
                st.error("⚠️ Inserisci il tuo nome prima di salvare!")
            else:
                try:
                    # USIAMO IL ROBOT PER SCRIVERE
                    foglio = connetti_gsheet()
                    
                    # Esempio di dati da salvare (Nome + una parola a caso per ora)
                    dati_da_salvare = [giocatore, "Dati Ricevuti!"] 
                    
                    foglio.append_row(dati_da_salvare)
                    st.success(f"✅ Grande {giocatore}! Pronostici salvati sul database.")
                    st.balloons()
                except Exception as e:
                    st.error(f"❌ Errore tecnico: {e}")

# --- 5. INTERFACCIA ADMIN ---
else:
    st.title("👑 Pannello Admin")
    st.write("Benvenuto nel centro di comando.")
    # Qui aggiungeremo la logica per calcolare la classifica
