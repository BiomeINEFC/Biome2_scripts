import streamlit as st
import pandas as pd
import numpy as np
from scipy.signal import butter, filtfilt
import matplotlib.pyplot as plt
import plotly.express as px
from scipy.signal import butter, lfilter, filtfilt
from scipy.signal import freqz
from scipy.signal import periodogram
from itertools import compress
from io import BytesIO

#FUNCTIONS#
def butter_bandpass(lowcut, highcut, fs, order, filter_type):
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    if filter_type == 'bandpass':
        b, a = butter(order, [low, high], btype='bandpass')
    elif filter_type == 'lowpass':
        b, a = butter(order, low, btype='lowpass')
    elif filter_type == 'highpass':
        b, a = butter(order, high, btype='highpass')
    return b, a

def butter_bandpass_filter(data, lowcut, highcut, fs, order, filter_type):
    b, a = butter_bandpass(lowcut, highcut, fs, order, filter_type)
    y = filtfilt(b, a, data)
    plt.figure()
    plt.plot(y)
    return y

def data_filter_butterworth_emg (data_frame, lowcut, highcut, data_freq, filter_order, filter_type):
    filt_data_frame = butter_bandpass_filter(data_frame.dropna(), lowcut, highcut, data_freq, filter_order, filter_type)                  
    return filt_data_frame






###################################
###############MAIN##################
st.title("Filttering APP")

st.markdown("""Aquesta APP serveig dur a terme filtratge de senyals""")
st.markdown("""Escull el tipus de filtres a realitzar.""")
# Definir les opcions del selector
opcions = ['lowpass', 'highpass', 'bandpass']

# Crear el selector desplegable
filter_type = st.selectbox('Tipus de filtre:', opcions)

if filter_type is not None:
    st.markdown("""Defineix la freqüència de mostreig i les freqüències de tall a utilitzar per dur a terme el filtre.""")
    
    data_freq = st.number_input(
        "Sampling Frequency",
        min_value=0,
        max_value=4000,
        value=0)
    lowcut = st.number_input(
        "Low cut frequency",
        min_value=0,
        max_value=int(data_freq/2),
        value=0)
    highcut = st.number_input(
        "High cut frequency",
        min_value=0,
        max_value=int(data_freq/2),
        value=0)
    filter_order = 4
    uploaded_file = None
    if data_freq != 0 and lowcut != 0 and highcut != 0:
        uploaded_file = st.file_uploader(
            "Selecciona el fitxer a filtrar",
            type=["xlsx"]
        )

if uploaded_file is not None:
    ##################################
    ########CONSTANTS#################


    
    raw_data = pd.read_excel(uploaded_file) 
    #FILTRATGE DADES
    dict_export = {}
    for col in raw_data:
        dict_export[col] = data_filter_butterworth_emg(raw_data[col], lowcut, highcut, data_freq, filter_order, filter_type)
    
   
    
    #EXPORTACIO
    export_df = pd.DataFrame(dict_export)

    output = BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        export_df.to_excel(
            writer,
            sheet_name='Filtered_data',
            index=False
        )
    
    output.seek(0)
    
    #Botó descàrrega
    st.download_button(
    label="Descarregar resultats",
    data=output.getvalue(),
    file_name="Filtered_data.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)