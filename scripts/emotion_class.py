from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import torch.nn.functional as F
import os

class Emotion_detector():

    def __init__(self):
        # Получаем путь к директории, где находится этот файл
        base_dir = os.path.dirname(os.path.abspath(__file__))
        # Собираем относительный путь к папке с моделью
        local_model_path = os.path.join(base_dir, "../ruBert_emotion_model")
        # Приводим к нормальной форме (убирает лишние ../)
        local_model_path = os.path.normpath(local_model_path)
        self.tokenizer = AutoTokenizer.from_pretrained(local_model_path)
        self.model = AutoModelForSequenceClassification.from_pretrained(local_model_path)


    def start(self, text:str):
        inputs = self.tokenizer(text, return_tensors="pt", truncation=True, padding=True)

        with torch.no_grad():
            outputs = self.model(**inputs)

        logits = outputs.logits
        probs = F.softmax(logits, dim=1)

        labels = self.model.config.id2label
        for i, prob in enumerate(probs[0]):
            print(f"{labels[i]}: {prob.item():.4f}")

        predicted_class_idx = torch.argmax(probs, dim=1).item()

        return  labels[predicted_class_idx]


