import sounddevice as sd
import numpy as np
import speech_recognition as sr
from queue import Queue, Empty
from threading import Event

class VoiceToTextConverter:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.recognizer.pause_threshold = 0.8
        self.sample_rate = 16000
        self.recognizer.energy_threshold = 4000
        self.stop_event = Event()
        self.audio_queue = Queue()
        self.stream = None

    def callback(self, indata, frames, time, status):
        if self.stop_event.is_set():
            raise sd.CallbackAbort
        self.audio_queue.put(indata.copy())

    def start_recording(self):
        self.stop_event.clear()
        self.audio_queue = Queue()
        self.stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=1,
            dtype='float32',
            callback=self.callback
        )
        self.stream.start()

    def stop_recording(self):
        self.stop_event.set()
        if self.stream:
            self.stream.close()
            self.stream = None

    def get_audio_data(self):
        audio_chunks = []
        while True:
            try:
                chunk = self.audio_queue.get_nowait()
                audio_chunks.append(chunk)
            except Empty:
                break
        
        return np.concatenate(audio_chunks) * 32767 if audio_chunks else None

    def audio_to_text(self, audio_data):
        if audio_data is None:
            return None

        audio_data = audio_data.astype(np.int16)
        audio_data = sr.AudioData(
            audio_data.tobytes(),
            sample_rate=self.sample_rate,
            sample_width=2
        )
        try:
            return self.recognizer.recognize_google(audio_data, language="ru-RU")
        except sr.UnknownValueError:
            raise RuntimeError("Речь не распознана")
        except sr.RequestError as e:
            raise RuntimeError(f"Ошибка сервиса: {e}")