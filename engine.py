import csv
import math
from pathlib import Path
from threading import Lock

MODEL_NAME = 'RobroKools/vad-bert'
ACTIONS = {'ask_clarification', 'acknowledge', 'offer_help', 'respect_boundary'}


def classify_scores(scores):
    if len(scores) != 3 or any(not math.isfinite(float(value)) for value in scores):
        raise ValueError('Le modèle doit renvoyer trois valeurs numériques finies.')
    valence, arousal, dominance = map(float, scores)
    if arousal > 3.5 and dominance > 3.0:
        return 'rejects_help'
    if valence < 2.5:
        return 'stays_negative'
    return 'opens_up'


def validate_request(data):
    if not isinstance(data, dict):
        raise ValueError('Une requête JSON objet est attendue.')
    text = data.get('user_text')
    action = data.get('current_system_action', 'ask_clarification')
    if not isinstance(text, str) or not text.strip():
        raise ValueError('Saisissez un texte en anglais.')
    if len(text) > 2000:
        raise ValueError('Le texte est limité à 2 000 caractères.')
    if not isinstance(action, str) or action not in ACTIONS:
        raise ValueError('Action de dialogue inconnue.')
    return text.strip(), action


class Analyzer:
    def __init__(self, directory):
        self.directory = Path(directory)
        self.tokenizer = None
        self.model = None
        self.lock = Lock()

    def scores(self, text):
        with self.lock:
            try:
                import torch
                from transformers import AutoModelForSequenceClassification, AutoTokenizer
            except ImportError as exc:
                raise RuntimeError('Dépendances manquantes. Lancez python -m pip install -r requirements.txt.') from exc
            if self.model is None:
                try:
                    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, local_files_only=True, trust_remote_code=False)
                    model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME, local_files_only=True, trust_remote_code=False, use_safetensors=False)
                    model.eval()
                except Exception as exc:
                    raise RuntimeError('Modèle indisponible dans le cache local. Lancez python download_model.py, puis réessayez.') from exc
                self.tokenizer, self.model = tokenizer, model
            inputs = self.tokenizer(text, return_tensors='pt', truncation=True, max_length=512)
            with torch.inference_mode():
                values = self.model(**inputs).logits.detach().cpu().reshape(-1).tolist()
            classify_scores(values)
            return values

    def next_action(self, current, reaction):
        path = self.directory / 'My_Aggregated_Logic.csv'
        if not path.is_file():
            return 'ask_clarification', 'fallback_missing_csv'
        required = {'Current_System_Action', 'User_Reaction', 'Next_System_Action'}
        with path.open(encoding='utf-8-sig', newline='') as stream:
            reader = csv.DictReader(stream)
            if not required.issubset(reader.fieldnames or []):
                raise ValueError('Colonnes CSV attendues : ' + ', '.join(sorted(required)))
            found = []
            for row in reader:
                if row['Current_System_Action'].strip() == current and row['User_Reaction'].strip() == reaction:
                    found.append(row['Next_System_Action'].strip())
            if len(set(found)) > 1:
                raise ValueError('La table CSV contient des décisions contradictoires pour cette situation.')
            if found:
                if found[0] not in ACTIONS:
                    return 'ask_clarification', 'fallback_unsupported_action'
                return found[0], 'csv'
        return 'ask_clarification', 'fallback_no_match'

    def analyze(self, data):
        text, current = validate_request(data)
        scores = self.scores(text)
        reaction = classify_scores(scores)
        action, source = self.next_action(current, reaction)
        return {
            'input_text': text,
            'vad_scores': dict(zip(('valence', 'arousal', 'dominance'), (round(v, 3) for v in scores))),
            'mapped_vad_state': reaction,
            'next_system_action': action,
            'decision_source': source,
            'model': MODEL_NAME,
            'method_note': 'Catégorie obtenue par les seuils du prototype, non validés comme mesure du comportement.',
        }

