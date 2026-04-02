import streamlit as st
import pandas as pd
import json

# --- CONFIGURAZIONE PAGINA E PASSWORD ---
st.set_page_config(page_title="Contest Mondiali 2026", page_icon="🏆", layout="centered")
PASSWORD_ADMIN = "mondiali2026"

# --- SIDEBAR: ACCESSO ADMIN ---
st.sidebar.title("👑 Area Admin")
admin_pass = st.sidebar.text_input("Password", type="password")

if admin_pass == PASSWORD_ADMIN:
    st.sidebar.success("Accesso Admin sbloccato!")
    admin_mode = True
else:
    admin_mode = False

# ==========================================
# VISTA UTENTE (I TUOI AMICI)
# ==========================================
if not admin_mode:
    st.title("🏆 Contest Mondiali 2026")
    st.markdown("Benvenuto! Inserisci il tuo nome e compila i risultati.")
    
    giocatore = st.text_input("Il tuo Nome o Nickname:")
    
    # Schede del gioco
    tab1, tab2, tab3 = st.tabs(["🌍 Fase a Gironi", "⚔️ Eliminazione Diretta", "🚀 Invia"])
    
    with tab1:
        st.write("Qui ci sarà la lista delle 72 partite con la grafica mobile-friendly (come vista prima).")
        # (Qui inseriremo il blocco delle caselline numeriche per i gironi)
        
    with tab2:
        st.write("Qui ci sarà il tasto 'Genera Tabellone' e i menu a tendina a cascata per Ottavi, Quarti, ecc.")
        # (Qui inseriremo il motore di calcolo e il tabellone knockout)
        
    with tab3:
        st.write("Invia i tuoi pronostici per registrarli nel database!")
        if st.button("Salva Pronostici", type="primary"):
            if not giocatore:
                st.error("Inserisci il tuo nome in alto!")
            else:
                st.success("Dati inviati correttamente al server!")
                # (Qui ci sarà il comando che usa st.secrets per scrivere su Google Sheets)

# ==========================================
# VISTA ADMIN (SOLO PER TE)
# ==========================================
else:
    st.title("👑 Pannello di Controllo Admin")
    st.warning("Sei in modalità Amministratore. I giocatori non vedono questa pagina.")
    
    tab_risultati, tab_classifica = st.tabs(["✏️ Inserisci Risultati Veri", "📊 Genera Classifica"])
    
    with tab_risultati:
        st.header("Risultati Ufficiali del Mondiale")
        st.write("Durante il mondiale, apri questa pagina e inserisci i risultati reali delle partite terminate.")
        # Esempio di come potrai inserire i dati reali comodamente dal sito
        st.text_input("Partita (es. Italia - Brasile)")
        st.text_input("Risultato Reale (es. 2-1)")
        if st.button("Salva Risultato Reale"):
            st.success("Risultato salvato nel database!")
            
    with tab_classifica:
        st.header("Classifica in Tempo Reale")
        st.write("Premi il bottone per far ricalcolare a Python i punteggi di tutti i partecipanti in base ai risultati ufficiali.")
        if st.button("🏆 Calcola Classifica Ufficiale", type="primary"):
            st.write("🔄 Elaborazione dati dal database...")
            
            # Qui il codice leggerà Google Sheets, farà i conti e stamperà la tabella:
            dati_finti = pd.DataFrame({
                "Posizione": [1, 2, 3],
                "Giocatore": ["Marco", "Luca", "Anna"],
                "Punti": [1250, 1100, 950]
            })
            st.dataframe(dati_finti, use_container_width=True)
            st.balloons() # Effetto festa di Streamlit!
