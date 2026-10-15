# -*- coding: utf-8 -*-
"""
Created on Fri Sep 25 11:06:15 2026

@author: blaif
"""

import streamlit as st
import wave
import tempfile
import os
from io import BytesIO

import numpy as np
import pandas as pd

from scipy.signal import resample
from wave import open as open_wave


def save_wav_channel(fn, wav, channel):
    """
    Guarda un únic canal d'un fitxer WAV multicanal.
    """

    nch = wav.getnchannels()
    depth = wav.getsampwidth()

    wav.setpos(0)
    sdata = wav.readframes(wav.getnframes())

    typ = {
        1: np.uint8,
        2: np.int16,
        4: np.int32
    }.get(depth)

    if typ is None:
        raise ValueError(
            f"Sample width {depth} bytes not supported"
        )

    if channel >= nch:
        raise ValueError(
            f"Cannot extract channel {channel+1} out of {nch}"
        )

    data = np.frombuffer(sdata, dtype=typ)

    ch_data = data[channel::nch]

    outwav = wave.open(fn, "wb")
    outwav.setparams(wav.getparams())
    outwav.setnchannels(1)
    outwav.writeframes(ch_data.tobytes())
    outwav.close()


def read_wav(file):
    """
    Llegeix un WAV i retorna:
    signal, sampling_rate
    """

    wav_file = open_wave(file, "rb")

    fs = wav_file.getframerate()

    nframes = wav_file.getnframes()

    wav_frames = wav_file.readframes(nframes)

    signal = np.frombuffer(
        wav_frames,
        dtype=np.int16
    )

    wav_file.close()

    return signal, fs


def resample_to_1000hz(signal, original_fs):

    n_samples_new = int(
        len(signal) * 1000 / original_fs
    )

    new_signal = resample(
        signal,
        n_samples_new
    )

    return new_signal


# -------------------------------------------------------------------------
# STREAMLIT APP
# -------------------------------------------------------------------------

st.title("WAV to EXCEL CONVERSION")

st.markdown(
    "Aquesta APP transforma fitxers WAV multicanal en un arxiu Excel."
)

uploaded_file = st.file_uploader(
    "Selecciona un fitxer WAV",
    type=["wav"]
)

if uploaded_file is not None:

    try:

        filename = uploaded_file.name
        base_name = filename.rsplit(".", 1)[0]

        temp_dir = tempfile.mkdtemp()

        wav = wave.open(uploaded_file, "rb")

        chan_n = wav.getnchannels()

        st.write(f"Canals detectats: {chan_n}")
        st.write(f"Freqüència original: {wav.getframerate()} Hz")

        wav_file_list = []

        for ch in range(chan_n):

            output_file = os.path.join(
                temp_dir,
                f"{base_name}_chan{ch+1}.wav"
            )

            save_wav_channel(
                output_file,
                wav,
                ch
            )

            wav_file_list.append(output_file)

        wav.close()

        chan_dict = {}

        progress_bar = st.progress(0)

        for i, file in enumerate(wav_file_list):

            signal, fs = read_wav(file)

            signal_1000 = resample_to_1000hz(
                signal,
                fs
            )

            column_name = f"Chan_{i+1}"

            chan_dict[column_name] = pd.Series(
                signal_1000
            )

            progress_bar.progress(
                (i + 1) / len(wav_file_list)
            )

        export_df = pd.DataFrame(chan_dict)

        st.success("Conversió completada")

        st.write("Vista prèvia dels primers registres:")

        st.dataframe(
            export_df.head(20)
        )

        output = BytesIO()

        with pd.ExcelWriter(
            output,
            engine="openpyxl"
        ) as writer:

            export_df.to_excel(
                writer,
                sheet_name="Results",
                index=False
            )

        output.seek(0)

        st.download_button(
            label="Descarregar Excel",
            data=output.getvalue(),
            file_name="Wav_transformed_to_Excel.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:

        st.error(
            f"Error durant el processament:\n{e}"
        )