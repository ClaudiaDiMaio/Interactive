import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import tempNcolor as t2c  # Assicurati che sia nella cartella streamlit_app

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Stellar Catalog Lab", layout="wide")

@st.cache_data
def load_data():
    # Caricamento dati (assicurati che la cartella 'data' sia presente nel tuo repo)
    try:
        # Nota: Ho aggiunto l'handling degli errori direttamente qui per sicurezza
        df = pd.read_csv('data/Hipparcos.csv')
        # Pre-calcolo colori basati su B-V
        df['hex_color'] = t2c.rgb2hex(t2c.bv2rgb(df['B-V']))
        return df
    except FileNotFoundError:
        st.error("❌ Errore: Non trovo il file 'data/Hipparcos.csv'. Controlla il percorso.")
        st.stop()
    except Exception as e:
        st.error(f"Errore nel caricamento dati o calcolo colori: {e}")
        st.stop()

# Tentativo di caricamento
df = load_data()


# --- SIDEBAR: CONTROLLI ---
st.sidebar.header("🕹️ Filtri Investigativi")

# Toggle per evidenziare stelle per distanza
dist_toggle = st.sidebar.checkbox("Evidenzia stelle per distanza", value=False)
dist_range = st.sidebar.slider(
    "Intervallo di Distanza (pc)", 
    min_value=0, 
    max_value=5000, 
    value=(1000, 1100),
    step=50
)

# --- LOGICA DI EVIDENZIAZIONE ---
# Definiamo le opacità e le dimensioni basandoci sulla selezione
if dist_toggle:
    # Modalità Investigativa: forte contrasto tra selezione e resto
    mask = (df['distance'] >= dist_range[0]) & (df['distance'] <= dist_range[1])
    # Stelle selezionate: grandi e opache. Altre: minuscole e quasi trasparenti.
    df['size'] = np.where(mask, 10, 4)
    df['opacity'] = np.where(mask, 1.0, 0.6)
else:
    # --- MODIFICA QUI ---
    # Modalità Normale: aumentiamo visibilità di base
    # Size 3 -> 5
    # Opacity 0.6 -> 0.9
    df['size'] = 5        
    df['opacity'] = 0.9  
    # --------------------

# --- FUNZIONE PER CREARE I GRAFICI ---
def create_star_chart(y_axis, title, y_label):
    fig = go.Figure()
    
    # Aggiungiamo le stelle utilizzando Scattergl per performance
    fig.add_trace(go.Scattergl(
        x=df['B-V'],
        y=df[y_axis],
        mode='markers',
        marker=dict(
            size=df['size'],
            color=df['hex_color'],
            opacity=df['opacity'],
            line=dict(width=0) # Rimuoviamo il bordo per pulizia
        ),
        text=df['HIP'], # Mostra ID Hipparcos all'hover
        hovertemplate="HIP: %{text}<br>B-V: %{x}<br>Valore: %{y}<extra></extra>"
    ))

    fig.update_layout(
        title=title,
        xaxis_title="Colore (B-V)",
        yaxis_title=y_label,
        yaxis_type="log", # Scala logaritmica obbligatoria per Luminosità
        template="plotly_dark",
        height=600, # Aumentato leggermente l'altezza
        margin=dict(l=20, r=20, t=40, b=20),
        xaxis=dict(range=[-0.5, 2.5])
    )
    return fig

# --- LAYOUT PRINCIPALE ---
st.title("🔭 Studio del Catalogo Hipparcos")
st.markdown("""
In questo modulo confrontiamo la **Luminosità intrinseca** (quanto la stella è potente) 
con la **Brillantezza apparente** (come la vediamo dalla Terra).
""")

col1, col2 = st.columns(2)

with col1:
    fig_hr = create_star_chart('Lum', 'Diagramma H-R (Potenza Reale)', 'Luminosità (L☉)')
    st.plotly_chart(fig_hr, use_container_width=True)

with col2:
    fig_bright = create_star_chart('Brightness', 'Brillantezza (Cosa vediamo)', 'Brillantezza (L☉/pc²)')
    st.plotly_chart(fig_bright, use_container_width=True)

# --- AREA DI ANALISI ---
if dist_toggle:
    st.info(f"✨ Stai evidenziando le stelle tra **{dist_range[0]}** e **{dist_range[1]}** parsec.")
    st.write("Nota come nel grafico di destra (Brillantezza) le stelle selezionate formino una linea netta, poiché sono tutte alla stessa distanza. Nel grafico di sinistra (Luminosità), invece, sono sparse su tutta la Sequenza Principale.")
