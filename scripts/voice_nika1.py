import sounddevice as sd  # Работа с микрофоном
import numpy as np
import speech_recognition as sr
from datetime import datetime
import streamlit as st


class VoiceToTextConverter:
    def init(self):
        self.recognizer = sr.Recognizer()
        self.recognizer.pause_threshold = 1.5
        self.sample_rate = 16000
        self.recognizer.energy_threshold = 4000

    def record_voice(self, duration=10):
        audio = sd.rec(
            int(duration * self.sample_rate),
            samplerate=self.sample_rate,
            channels=1,
            dtype='float32'
        )
        sd.wait()
        return (audio * 32767).astype(np.int16)

    def audio_to_text(self, audio_data):
        audio_data = sr.AudioData(
            audio_data.tobytes(),
            sample_rate=self.sample_rate,
            sample_width=2
        )
        try:
            return self.recognizer.recognize_google(audio_data, language="ru-RU")
        except Exception as e:
            st.error(f"Ошибка распознавания: {str(e)}")
            return None


if name == "main":
    vtt = VoiceToTextConverter()
    vtt.process_voice_note()