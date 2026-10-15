import streamlit as st
import pandas as pd
import numpy as np
from scipy.signal import butter, filtfilt
import matplotlib.pyplot as plt
import plotly.express as px
from scipy.signal import butter, lfilter, filtfilt
from scipy.signal import freqz
from scipy.signal import periodogram

#FUNCTIONS#
def butter_bandpass(lowcut, highcut, fs, order, filter_type):
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    if filter_type == 'band':
        b, a = butter(order, [low, high], btype='bandpass')
    elif filter_type == 'low':
        b, a = butter(order, low, btype='lowpass')
    return b, a

def butter_bandpass_filter(data, lowcut, highcut, fs, order, filter_type):
    b, a = butter_bandpass(lowcut, highcut, fs, order, filter_type)
    y = filtfilt(b, a, data)
    plt.figure()
    plt.plot(y)
    return y

def data_filter_butterworth_emg (data_frame, lowcut, highcut, data_freq, filter_order):
    filt_data_frame = butter_bandpass_filter(data_frame.dropna(), lowcut, highcut, data_freq, filter_order, 'band')                  
    return filt_data_frame

def RMS_calculation (EMG_signal, computation_onsets, computation_offsets):
    muscle_RMS = []
    analysis_window = (computation_offsets[0] - computation_onsets[0])
    for i in range(0,len(computation_onsets)):
        muscle_RMS.append ((np.sum(np.square(EMG_signal[computation_onsets[i]:computation_offsets[i]]))/analysis_window)**0.5)
    return pd.DataFrame({'x': ['0-20%', '20-40%', '40-60%', '60-80%', '80-100%'], 'y': muscle_RMS})
def mean_median_frequency_computation (EMG_onsets, EMG_offsets, data_frame_nAbs, muscle):
    mean_freq_data = list()
    median_freq_data = list()
    number_of_plots = len(EMG_onsets)+2
    number_of_rows = 30
    number_of_cols = 3
    fig, ax = plt.subplots(number_of_rows, number_of_cols)
    col_num = 0
    row_num = 0
    for frame in range(0, len(EMG_onsets)):
        onset = EMG_onsets[frame]
        offset = EMG_offsets[frame]
        sampling_rate = 1000
        signal= data_frame_nAbs[onset:offset]
        freqs, power = periodogram(signal, fs=sampling_rate, window='hamming')
        ax[row_num][col_num].plot(freqs, power)
        ax[row_num][col_num].set_title('PSD - Stage: ' + str(frame*20) +' to '+str(frame*20+20) +' - '+muscle)
        recur_sum_power = list ()
        for frame in range(0, len(freqs)):
            if recur_sum_power == []:
                recur_sum_power.append(power[frame])
            else:
                recur_sum_power.append(recur_sum_power[-1]+power[frame])
        median_freq_data.append(list(compress(freqs, recur_sum_power>=recur_sum_power[-1]/2))[0]) 
        mean_freq_data.append(np.sum(freqs*power)/np.sum(power))
        row_num = row_num + 1
        if row_num >29:
            row_num = 0
            col_num = col_num + 1
    return pd.DataFrame({'x': ['0-20%', '20-40%', '40-60%', '60-80%', '80-100%'], 'y':mean_freq_data}), pd.DataFrame({'x': ['0-20%', '20-40%', '40-60%', '60-80%', '80-100%'], 'y':median_freq_data})





###################################
###############MAIN##################
st.title("EMG FATIGUE ANALYSIS APP")

st.markdown("""Aquesta APP serveig per fer l'anàlisi de residus d'una senyal. """)
st.mark
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