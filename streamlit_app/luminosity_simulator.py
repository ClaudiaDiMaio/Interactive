import streamlit as st
import numpy as np
import plotly.graph_objects as go
import tempNcolor as tc  # Assicurati che sia nella stessa cartella
import number_formatting as nf # Assicurati che sia nella stessa cartella

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Stellar Lab 2026", layout="wide")

# --- COSTANTI ---
M_SUN = 4.83  
T_SUN = 5777  

# --- FUNZIONI DI SUPPORTO ---
def get_spectral_info(t_ratio):
    temp = t_ratio * T_SUN
    if temp > 30000: return "O", "Blu (Caldissima)", "#9bb0ff"
    if temp > 10000: return "B", "Azzurra", "#aabfff"
    if temp > 7500:  return "A", "Bianca", "#cad7ff"
    if temp > 6000:  return "F", "Bianco-Gialla", "#f8f7ff"
    if temp > 5200:  return "G", "Gialla (Tipo Sole)", "#fff4ea"
    if temp > 3700:  return "K", "Arancione", "#ffd2a1"
    return "M", "Rossa (Fredda)", "#ffcc6f"

# --- INTERFACCIA SIDEBAR ---
st.sidebar.header("🕹️ Pannello di Controllo")
st.sidebar.markdown("Modifica i parametri per creare la tua stella:")
t_ratio = st.sidebar.slider("Temperatura (T/T☉)", 0.5, 7.0, 1.0, step=0.1)
r_ratio = st.sidebar.slider("Raggio (R/R☉)", 0.1, 20.0, 1.0, step=0.1)

# --- LOGICA FISICA ---
lum_ratio = (r_ratio**2) * (t_ratio**4)
m_abs = M_SUN - 2.5 * np.log10(lum_ratio) if lum_ratio > 0 else 20.0
t_kelvin = int(t_ratio * T_SUN)
spec_class, spec_desc, hex_color = get_spectral_info(t_ratio)

# --- LAYOUT PRINCIPALE ---
st.title("🕵️‍♂️ L'Investigatore Stellare")
st.subheader(f"Risultato Analisi: Stella di Classe {spec_class} — {spec_desc}")

col_grafico, col_dati = st.columns([2, 1])

with col_grafico:
    # Rappresentazione visiva con Plotly (Sostituisce pythreejs)
    # Mostriamo la stella e il Sole di confronto
    fig = go.Figure()
    
    # Stella Modello
    fig.add_trace(go.Scatter(
        x=[0], y=[0], mode='markers',
        marker=dict(size=r_ratio*15, color=hex_color, line=dict(width=2, color='white')),
        name="Stella Modello"
    ))
    
    # Sole di confronto (fisso a destra)
    fig.add_trace(go.Scatter(
        x=[25], y=[0], mode='markers',
        marker=dict(size=15, color='#fff4ea', opacity=0.3, line=dict(width=1, color='gray')),
        name="Sole"
    ))
    
    fig.update_layout(
        title="Confronto Dimensionale (Stella vs Sole)",
        template="plotly_dark",
        xaxis=dict(visible=False, range=[-20, 40]),
        yaxis=dict(visible=False, range=[-20, 20]),
        height=450,
        showlegend=True
    )
    st.plotly_chart(fig, use_container_width=True)

with col_dati:
    st.write("### 📊 Dati Scientifici")
    st.metric("Temperatura", f"{t_kelvin} K")
    st.metric("Luminosità", f"{lum_ratio:.2f} L☉")
    st.metric("Magnitudine Assoluta (M)", f"{m_abs:.2f}")
    
    st.divider()
    st.write("**Nota dell'astronomo:**")
    if m_abs < 0:
        st.success("Questa stella è una vera gigante del cielo!")
    elif m_abs > 10:
        st.warning("Questa stella è molto debole (Nana).")
    else:
        st.info("Stella di dimensioni medie.")

# --- BARRA DI POTENZA LOGARITMICA ---
st.write("### ⚡ Potenza Emessa Totale")
# Una barra che mostra dove si colloca la stella (scala logaritmica)
power_level = np.clip((np.log10(lum_ratio) + 4) / 10, 0.0, 1.0)
st.progress(power_level)
st.caption("Dalle Nane Brune (Sinistra) alle Supergiganti (Destra)")
