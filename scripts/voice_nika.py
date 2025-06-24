"""
@file
@brief Класс для преобразования речи в текст с помощью SoundDevice и SpeechRecognition.
@details
Позволяет записывать аудио с микрофона, сохранять его в буфер и распознавать текст через Google Speech Recognition API.
"""

import sounddevice as sd
import numpy as np
import speech_recognition as sr
from queue import Queue, Empty
from threading import Event


class VoiceToTextConverter:
    """
    @brief Класс для записи и распознавания речи с микрофона.

    @details
    Позволяет записывать звук с микрофона, управлять процессом записи, собирать аудиоданные и преобразовывать их в текст (русский язык).
    """

    def __init__(self):
        """
        @brief Инициализация конвертера.
        @details
        Создаёт recognizer, очередь для аудиоданных, событие для остановки и поток записи.
        """
        self.recognizer = sr.Recognizer()
        self.recognizer.pause_threshold = 0.8
        self.sample_rate = 16000
        self.recognizer.energy_threshold = 4000
        self.stop_event = Event()
        self.audio_queue = Queue()
        self.stream = None

    def callback(self, indata, frames, time, status):
        """
        @brief Callback-функция для SoundDevice InputStream.

        @param indata Входящий аудиофрейм.
        @param frames Количество фреймов.
        @param time Временная метка.
        @param status Статус захвата.
        @details
        Кладёт аудиоданные в очередь. Прерывает поток при установленном событии остановки.
        """
        if self.stop_event.is_set():
            raise sd.CallbackAbort
        self.audio_queue.put(indata.copy())

    def start_recording(self):
        """
        @brief Начинает запись аудио с микрофона.

        @details
        Очищает событие остановки и очередь, и запускает новый InputStream.
        """
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
        """
        @brief Останавливает запись аудио.

        @details
        Устанавливает событие остановки, закрывает InputStream.
        """
        self.stop_event.set()
        if self.stream:
            self.stream.close()
            self.stream = None

    def get_audio_data(self):
        """
        @brief Получает все накопленные аудиоданные из очереди.

        @return Numpy-массив аудиоданных (int16) или None, если данных нет.
        """
        audio_chunks = []
        while True:
            try:
                chunk = self.audio_queue.get_nowait()
                audio_chunks.append(chunk)
            except Empty:
                break

        return np.concatenate(audio_chunks) * 32767 if audio_chunks else None

    def audio_to_text(self, audio_data):
        """
        @brief Преобразует аудиомассив в текст с помощью Google Speech Recognition.

        @param audio_data Numpy-массив аудиоданных (int16).
        @return Распознанный текст (str) или None, если аудиоданных нет.
        @throws RuntimeError Если речь не распознана или возникла ошибка сервиса.
        """
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
