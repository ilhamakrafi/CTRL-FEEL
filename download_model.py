from transformers import AutoModelForSequenceClassification, AutoTokenizer
from engine import MODEL_NAME

if __name__ == '__main__':
    print('Téléchargement initial du modèle depuis Hugging Face…')
    AutoTokenizer.from_pretrained(MODEL_NAME, trust_remote_code=False)
    AutoModelForSequenceClassification.from_pretrained(MODEL_NAME, trust_remote_code=False, use_safetensors=False)
    print('Modèle disponible. Lancez python server.py.')

