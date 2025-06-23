from transformers import AutoTokenizer, AutoModelForSequenceClassification


model_name = "MaxKazak/ruBert-base-russian-emotion-detection"

save_directory = "./ruBert_emotion_model"


tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSequenceClassification.from_pretrained(model_name)


tokenizer.save_pretrained(save_directory)
model.save_pretrained(save_directory)

print(f"Сохранено в: {save_directory}")
