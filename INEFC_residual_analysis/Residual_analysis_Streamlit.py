import streamlit as st
import pandas as pd
import numpy as np
from scipy.signal import butter, filtfilt
import matplotlib.pyplot as plt
import plotly.express as px
from scipy.signal import butter, lfilter, filtfilt
from scipy.signal import freqz
from scipy.signal import periodogram





###################################
###############MAIN##################
st.title("EMG FATIGUE ANALYSIS APP")

st.markdown("""Aquesta APP serveig per fer l'anàlisi de residus d'una senyal. """)
st.markdown("""Indica la freqüència de mostreig de les dades i les freqüències entre les que vols realitzar l'anàlisi de residus i quin increment de freqüència vols utilitzar.""")

Fs = st.number_input(
    "Freqüència de mostreig",
    min_value=0,
    max_value=4000,
    value=0)
lowcut = st.number_input(
    "Freqüència més baixa",
    min_value=0,
    max_value=int(Fs/2),
    value=0)
highcut = st.number_input(
    "Freqüència més alta",
    min_value=0,
    max_value=int(Fs/2),
    value=0)
increments = st.number_input(
    "Increment entre freqüèncias - habitualment 1Hz",
    min_value = 0.0001,
    max_value = 20,
    value = 1)


results = []
order = 4
uploaded_file = None
if Fs != 0 and lowcut != 0 and highcut != 0:
    uploaded_file = st.file_uploader(
        "Selecciona el fitxer excel amb la senyal - Ha de contenir una única columna de dades i amb la capçalera: Data",
        type=["xlsx"]
    )

if uploaded_file is not None:
    ##################################
    ########CONSTANTS#################
    freqs = np.arange (lowcut, highcut, increments)
    residual_var = np.zeros(len(freqs))

    senyal = pd.read_excel(uploaded_file)
    for i, freq in enumerate(freqs):
    
        Wn = freq / (Fs / 2)
    
        if Wn >= 1:
            residual_var[i] = np.nan
            continue
    
        try:
            b, a = butter(order, Wn, btype='low')
    
            filtrada = filtfilt(b, a, senyal)
            residual = senyal - filtrada
    
            residual_var[i] = np.var(residual)
    
        except:
            residual_var[i] = np.nan
    
    # limpiar NaN
    valid = ~np.isnan(residual_var)
    freqs_valid = freqs[valid]
    residual_var = residual_var[valid]
    
    # ---------------------------
    # METODO DEL CODO
    # ---------------------------
    x = (freqs_valid - freqs_valid.min()) / (freqs_valid.max() - freqs_valid.min())
    y = (residual_var - residual_var.min()) / (residual_var.max() - residual_var.min())
    
    p1 = np.array([x[0], y[0]])
    p2 = np.array([x[-1], y[-1]])
    
    line_vec = p2 - p1
    line_vec /= np.linalg.norm(line_vec)
    
    distances = []
    
    for i in range(len(x)):
        point = np.array([x[i], y[i]])
        vec = point - p1
    
        proj_len = np.dot(vec, line_vec)
        proj_point = p1 + proj_len * line_vec
    
        distances.append(np.linalg.norm(point - proj_point))
    
    distances = np.array(distances)
    
    idx_opt = np.argmax(distances)
    f_opt = freqs_valid[idx_opt]
    
    results.append(f_opt)
    
    
    
    
    # Crear figura
    
    df = pd.DataFrame({
    'freq': freqs_valid,
    'residual_var': residual_var
    })
    
    fig = px.line(
        df,
        x='freq',
        y='residual_var',
        title=f'Residual analysis'
    )
    
    # Punt òptim en vermell
    fig.add_scatter(
        x=[f_opt],
        y=[residual_var[idx_opt]],
        mode='markers',
        marker=dict(color='red', size=10),
        name='f_opt'
    )
    
    fig.update_layout(
        xaxis_title='Frecuencia (Hz)',
        yaxis_title='Variança residual',
        template='plotly_white'
    )
    
    fig.show()



    # st.plotly_chart(fig, use_container_width=True)
    
    
    #EXPORTACIO
#     export_df = pd.concat([RMS_df, MNF_df['y'], MDF_df['y']], axis=1)
#     export_df.columns=names=['Periods', 'RMS', 'MNF', 'MDF']

#     output = BytesIO()
    
#     with pd.ExcelWriter(output, engine='openpyxl') as writer:
#         export_df.to_excel(
#             writer,
#             sheet_name='Results',
#             index=False
#         )
    
#     output.seek(0)
    
#     #Botó descàrrega
#     st.download_button(
#     label="Descarregar resultats",
#     data=output.getvalue(),
#     file_name="EMG_fatigue_results.xlsx",
#     mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
# )