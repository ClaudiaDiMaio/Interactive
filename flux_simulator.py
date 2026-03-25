# --- BLOCK 1: Import e Definizioni ---
import ipywidgets as widgets
import bqplot as bq
import numpy as np
import tempNcolor as tc  # Assumendo sia presente nell'ambiente
import number_formatting as nf  # Assumendo sia presente nell'ambiente
from IPython.display import display, clear_output

# Costanti e Modello Stella Sequenza Principale [cite: 751, 912]
Lvs_R_coeff = [-14.414732200764211, -13.259918928247322, 88.94347154444976, -24.088776726372608, 
               -87.71861646290176, 31.910048976800123, 30.045785739826723, -10.017454060166651, 
               -1.7461666512820873, 5.534581622863519, -0.06725347697088192]
LogLum = np.poly1d(Lvs_R_coeff)

def find_flux(l, r):
    # Legge dell'inverso del quadrato [cite: 244, 257, 645]
    return l / (4 * np.pi * (r ** 2))

def L_given_R(radius):
    logR = np.log10(radius)
    return 10**LogLum(logR)

# --- BLOCK 2: Creazione Widget ---
Dist_PC = widgets.FloatSlider(description='Distanza (pc):', min=1.0, max=10.0, step=0.1, value=1.0)
Rad = widgets.FloatSlider(description='Raggio (R☉):', min=0.1, max=2.0, step=0.1, value=1.0)

Luminosity = widgets.Text(description='Luminosità (L☉):', disabled=True)
Flux = widgets.Text(description='Flusso:', disabled=True)

# Nuovo: Fotometro visivo
Photometer = widgets.FloatProgress(value=0, min=0, max=1.0, description='Fotometro:', 
                                   bar_style='info', orientation='horizontal')

# Nuovo: Area Identikit
out_identikit = widgets.Output()
btn_identikit = widgets.Button(description="Genera Identikit Stellare", button_style='success')

# --- BLOCK 3: Logica di Aggiornamento (W) ---
def update_view(change=None):
    d = Dist_PC.value
    r = Rad.value
    lum = L_given_R(r)
    flux_val = find_flux(lum, d)
    
    # Aggiorna Testi [cite: 353-359]
    Luminosity.value = str(round(lum, 3))
    Flux.value = str(round(flux_val, 5))
    
    # Aggiorna Fotometro e colore (Saturazione)
    Photometer.value = min(flux_val * 10, 1.0)
    Photometer.bar_style = 'danger' if Photometer.value > 0.8 else 'info'
    
    # Calcolo Temperatura e Colore [cite: 101, 645, 649]
    Temp = pow(lum/(r*r), 0.25)*5777
    hexcolor = tc.rgb2hex(tc.temp2rgb(Temp))[0]
    
    # Effetto GLOW: la dimensione cambia con il flusso ricevuto
    star_earth.default_size = int(20 + (flux_val * 500)) 
    star_earth.colors = [hexcolor]
    star_earth.default_opacities = [min(0.2 + flux_val, 1.0)]
    
    # Stella reale (Luminosità intrinseca)
    star.colors = [hexcolor]
    star.default_size = int(r * 500)

Dist_PC.observe(update_view, names='value')
Rad.observe(update_view, names='value')

# Azione Pulsante Identikit
def on_button_clicked(b):
    with out_identikit:
        clear_output()
        lum = float(Luminosity.value)
        r = float(Rad.value)
        temp = int(pow(lum/(r*r), 0.25)*5777)
        # Classificazione approssimativa [cite: 756-779]
        tipo = "O" if temp > 30000 else "B" if temp > 10000 else "A" if temp > 7500 else "F" if temp > 6000 else "G" if temp > 5200 else "K" if temp > 3700 else "M"
        print(f"--- IDENTIKIT DELL'INVESTIGATORE ---")
        print(f"Tipo Spettrale stimato: {tipo}")
        print(f"Temperatura Superficiale: {temp} K")
        print(f"Distanza: {Dist_PC.value} pc")
        print(f"Nota: Questa stella emette {round(lum, 2)} volte l'energia del Sole.")

btn_identikit.on_click(on_button_clicked)

# --- BLOCK 4: Layout Grafico (bqplot) ---
sc_x, sc_y = bq.LinearScale(), bq.LinearScale()
star = bq.Scatter(x=[5], y=[5], scales={'x': sc_x, 'y': sc_y}, default_size=1000)
star_earth = bq.Scatter(x=[5], y=[5], scales={'x': sc_x, 'y': sc_y}, default_size=20)

fig_lum = bq.Figure(title='Sorgente (Potenza Reale)', marks=[star], background_style={'fill':'black'})
fig_flux = bq.Figure(title='Telescopio (Flusso Ricevuto)', marks=[star_earth], background_style={'fill':'black'})

# --- DISPLAY ---
layout_controlli = widgets.VBox([Dist_PC, Rad, Luminosity, Flux, Photometer, btn_identikit])
layout_visual = widgets.HBox([fig_lum, fig_flux])
display(widgets.VBox([layout_visual, layout_controlli, out_identikit]))

update_view() # Inizializzazione
