import pandas as pd
import torch, json
from transformers import AutoTokenizer, AutoModelForSequenceClassification

# ==========================================
# 1. CHARGEMENT DE LA LOGIQUE (Notre mode d'emploi)
# ==========================================
try:
    # On lit le fichier CSV contenant les décisions de la classe.
    logic_df = pd.read_csv('My_Aggregated_Logic.csv')
except FileNotFoundError:
    print("Erreur : 'My_Aggregated_Logic.csv' est introuvable.")
    logic_df = pd.DataFrame()


def get_next_action(current_action, user_reaction):
    """Cherche l'action suivante recommandée selon le consensus."""
    if logic_df.empty: return "ask_clarification"

    match = logic_df[(logic_df['Current_System_Action'] == current_action) &
                     (logic_df['User_Reaction'] == user_reaction)]

    if not match.empty:
        return match.iloc[0]['Next_System_Action']
    else:
        return "ask_clarification"

    # ==========================================


# 2. PRÉPARATION DU MODÈLE VAD-BERT (Le lecteur continu)
# ==========================================
print("Chargement du modèle VAD-BERT (cela peut prendre quelques secondes)...")
# Ce modèle ne donne plus des mots ("joie", "tristesse"), mais 3 chiffres : Valence, Arousal, Dominance.
model_name = "RobroKools/vad-bert"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSequenceClassification.from_pretrained(model_name)


# ==========================================
# 3. TRADUCTION DES SCORES VAD (Mathématiques)
# ==========================================
def predict_user_reaction(text):
    """
    Donne le texte à l'IA, récupère les 3 scores (Valence, Arousal, Dominance),
    et utilise des règles mathématiques pour classer l'utilisateur dans l'un de nos 3 états.
    """
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True)

    with torch.no_grad():
        outputs = model(**inputs)

    # Le modèle recrache une liste de 3 nombres correspondant à [Valence, Arousal, Dominance].
    # Sur ce modèle, les scores vont de 1 (très bas) à 5 (très haut).
    vad_scores = outputs.logits.detach().squeeze().tolist()
    valence, arousal, dominance = vad_scores[0], vad_scores[1], vad_scores[2]

    # --- LA LOGIQUE DES SEUILS ---
    # Au lieu d'un dictionnaire, on utilise des conditions (if) sur les chiffres.

    # Règle 1 : Rejet de l'aide (Rejects Help)
    # L'utilisateur est agité (Arousal élevé) et cherche à reprendre le contrôle (Dominance élevée).
    if arousal > 3.5 and dominance > 3.0:
        custom_reaction = "rejects_help"

    # Règle 2 : Reste négatif / Triste (Stays Negative)
    # L'utilisateur se sent mal (Valence basse). On peut aussi ajouter une dominance basse (impuissance),
    # mais la valence basse est le signal principal.
    elif valence < 2.5:
        custom_reaction = "stays_negative"

    # Règle 3 : S'ouvre / Positif (Opens Up)
    # Si la valence est neutre ou positive (pas de détresse) et qu'il n'est pas en train de rejeter l'aide.
    else:
        custom_reaction = "opens_up"

    # On prépare un dictionnaire propre pour afficher les scores bruts dans la réponse.
    raw_vad = {
        "valence": round(valence, 2),
        "arousal": round(arousal, 2),
        "dominance": round(dominance, 2)
    }

    return raw_vad, custom_reaction


# ==========================================
# 4. EXÉCUTION DU SYSTÈME (Gestion JSON)
# ==========================================
def process_json_request(json_payload):
    """Reçoit la requête JSON, la traite avec VAD, et renvoie une réponse JSON."""

    try:
        data = json.loads(json_payload)
        user_text = data.get("user_text", "")
        current_system_action = data.get("current_system_action", "ask_clarification")
    except json.JSONDecodeError:
        return json.dumps({"error": "Le format JSON fourni est invalide."})

    # On récupère les scores VAD bruts et l'état calculé.
    raw_vad_scores, mapped_reaction = predict_user_reaction(user_text)

    # L'Oracle trouve la suite.
    next_action = get_next_action(current_system_action, mapped_reaction)

    # On prépare la réponse JSON en incluant les 3 scores mathématiques.
    response = {
        "input_text": user_text,
        "vad_scores": raw_vad_scores,
        "mapped_vad_state": mapped_reaction,
        "next_system_action": next_action
    }

    # On retourne un JSON propre (jamais de pprint() ici !)
    return json.dumps(response, indent=2)


if __name__ == "__main__":
    print("\n--- Test du pipeline VAD ---")

    mock_incoming_json = '''
    {
        "user_text": "Leave me alone, your advice is completely useless!",
        "current_system_action": "acknowledge"
    }
    '''

    print("Requête JSON entrante :")
    print(mock_incoming_json)

    outgoing_json_response = process_json_request(mock_incoming_json)

    print("\nRéponse JSON sortante :")
    print(outgoing_json_response)