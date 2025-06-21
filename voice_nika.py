import sounddevice as sd  # Работа с микрофоном
import numpy as np  # Обработка аудиоданных
import speech_recognition as sr  # Распознавание речи
from datetime import datetime  # Для временных меток


class VoiceToTextConverter:
    def __init__(self):
        self.recognizer = sr.Recognizer()  # Инициализация распознавателя
        self.recognizer.pause_threshold = 1.5  # Пауза для конца фразы (сек)
        self.sample_rate = 16000  # Оптимальная частота для распознавания
        self.recognizer.energy_threshold = 4000  # Чувствительность микрофона

    def record_voice(self, duration=10):
        """Запись аудио с микрофона"""
        print(f"\n🎤 Запись... (макс. {duration} сек)")
        audio = sd.rec(  # Запись в буфер
            int(duration * self.sample_rate),  # Кол-во сэмплов
            samplerate=self.sample_rate,  # Частота дискретизации
            channels=1,  # Моно-запись
            dtype='float32'  # Формат данных
        )
        sd.wait()  # Ожидание окончания записи
        return audio

    def save_as_text(self, text, filename="voice_notes.txt"):
        """Сохранение текста в файл"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")  # Текущее время
        with open(filename, "a", encoding="utf-8") as f:  # Открытие файла
            f.write(f"[{timestamp}]\n{text}\n\n")  # Запись с меткой времени
        print(f"✅ Текст сохранен в {filename}")

    def process_voice_note(self):
        """Полный цикл записи и распознавания"""
        try:
            # 1. Запись аудио
            audio = self.record_voice(duration=10)

            # 2. Конвертация в 16-битный формат
            audio_int16 = (audio * 32767).astype(np.int16)  # Нормализация

            # 3. Подготовка данных для распознавания
            audio_data = sr.AudioData(
                audio_int16.tobytes(),  # Байтовый поток
                sample_rate=self.sample_rate,  # Частота
                sample_width=2  # 16-бит = 2 байта
            )

            # 4. Распознавание через Google API
            text = self.recognizer.recognize_google(audio_data, language="ru-RU")
            print("\n📝 Текст:", text)

            # 5. Сохранение результата
            self.save_as_text(text)
            return text

        except sr.UnknownValueError:  # Не распознана речь
            print("❌ Речь не распознана")
        except sr.RequestError as e:  # Ошибка API
            print(f"❌ Ошибка сервиса: {e}")
        except Exception as e:  # Другие ошибки
            print(f"❌ Ошибка: {e}")
        return None


# Пример использования
if __name__ == "__main__":
    vtt = VoiceToTextConverter()  # Создаем конвертер
    vtt.process_voice_note()  # Запускаем процесс