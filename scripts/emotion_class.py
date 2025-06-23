from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import torch.nn.functional as F

class Emotion_detector():

    def __init__(self):
        local_model_path = "D:/project/Python25/ruBert_emotion_model"
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


text = "Я купил мороженое. У меня было хорошее настроение и в этот день я получил зачёт по математике"
detekrot = Emotion_detector()

print(detekrot.start(text))
