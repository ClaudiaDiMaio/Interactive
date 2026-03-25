import streamlit as st
import numpy as np
import plotly.graph_objects as go
import tempNcolor as tc  # Assicurati che il file sia nella stessa cartella
import number_formatting as nf # Assicurati che il file sia nella stessa cartella

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Laboratorio Stellare", layout="wide")
st.title("🕵️‍♂️ L'Investigatore della Luce: Identikit Stellare")

# --- MODELLO FISICO (Dati originali) ---
Lvs_R_coeff = [-14.414732200764211, -13.259918928247322, 88.94347154444976, -24.088776726372608, 
               -87.71861646290176, 31.910048976800123, 30.045785739826723, -10.017454060166651, 
               -1.7461666512820873, 5.534581622863519, -0.06725347697088192]
LogLum = np.poly1d(Lvs_R_coeff)

def find_flux(l, r):
    return l / (4 * np.pi * (r ** 2))

def L_given_R(radius):
    logR = np.log10(radius)
    return 10**LogLum(logR)

# --- SIDEBAR (Controlli) ---
st.sidebar.header("Parametri di Osservazione")
dist_pc = st.sidebar.slider("Distanza (pc)", 1.0, 10.0, 1.0, step=0.1)
rad_solar = st.sidebar.slider("Raggio (R☉)", 0.1, 2.0, 1.0, step=0.1)

# --- CALCOLI ---
lum = L_given_R(rad_solar)
flux_val = find_flux(lum, dist_pc)
temp = pow(lum/(rad_solar**2), 0.25) * 5777
hexcolor = tc.rgb2hex(tc.temp2rgb(temp))[0]

# --- LAYOUT VISUALE ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("Sorgente (Potenza Reale)")
    fig_src = go.Figure(go.Scatter(x=[0], y=[0], mode='markers',
                                   marker=dict(size=rad_solar*100, color=hexcolor, 
                                               line=dict(width=2, color='white'))))
    fig_src.update_layout(xaxis=dict(visible=False), yaxis=dict(visible=False), 
                          template="plotly_dark", height=300, margin=dict(l=20, r=20, t=20, b=20))
    st.plotly_chart(fig_src, use_container_width=True)
    st.metric("Luminosità", f"{lum:.3f} L☉")

with col2:
    st.subheader("Telescopio (Flusso Ricevuto)")
    # Effetto bagliore basato sul flusso
    glow_size = int(20 + (flux_val * 200))
    fig_tel = go.Figure(go.Scatter(x=[0], y=[0], mode='markers',
                                   marker=dict(size=glow_size, color=hexcolor, 
                                               opacity=min(0.2 + flux_val, 1.0))))
    fig_tel.update_layout(xaxis=dict(visible=False), yaxis=dict(visible=False), 
                          template="plotly_dark", height=300, margin=dict(l=20, r=20, t=20, b=20))
    st.plotly_chart(fig_tel, use_container_width=True)
    st.metric("Flusso misurato", f"{flux_val:.5f}")

# --- FOTOMETRO ---
st.write("### Fotometro")
photo_val = min(flux_val * 10, 1.0)
st.progress(photo_val)
if photo_val > 0.8:
    st.warning("⚠️ ATTENZIONE: Sensore in saturazione! La stella è troppo luminosa.")

# --- IDENTIKIT ---
st.divider()
if st.button("🔍 Genera Identikit Stellare", type="primary"):
    tipo = "O" if temp > 30000 else "B" if temp > 10000 else "A" if temp > 7500 else "F" if temp > 6000 else "G" if temp > 5200 else "K" if temp > 3700 else "M"
    
    st.success("### Risultati dell'Analisi")
    c1, c2, c3 = st.columns(3)
    c1.write(f"**Tipo Spettrale:** {tipo}")
    c2.write(f"**Temperatura:** {int(temp)} K")
    c3.write(f"**Distanza:** {dist_pc} pc")
    st.info(f"Nota: Questa stella emette {lum:.2f} volte l'energia del Sole.")
