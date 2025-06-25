"""
@file
@brief Загрузка и сохранение модели ruBERT для определения эмоций.
@details
Скачивает модель и токенизатор с HuggingFace Hub и сохраняет их в локальную папку для дальнейшего использования офлайн.
"""

from transformers import AutoTokenizer, AutoModelForSequenceClassification

#: @brief Имя модели HuggingFace для загрузки.
model_name = "MaxKazak/ruBert-base-russian-emotion-detection"

#: @brief Папка для сохранения модели и токенизатора.
save_directory = "./ruBert_emotion_model"

#: @brief Загрузка токенизатора из HuggingFace Hub.
tokenizer = AutoTokenizer.from_pretrained(model_name)

#: @brief Загрузка модели для классификации последовательностей.
model = AutoModelForSequenceClassification.from_pretrained(model_name)

#: @brief Сохранение токенизатора и модели в указанную папку.
tokenizer.save_pretrained(save_directory)
model.save_pretrained(save_directory)

print(f"Сохранено в: {save_directory}")
