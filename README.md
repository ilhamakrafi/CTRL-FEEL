# CTRL+FEEL — Interface locale

CTRL+FEEL est une interface web locale pour le prototype d’analyse émotionnelle **VAD-BERT**. Elle permet de saisir un texte, d’obtenir les scores de valence, d’activation et de dominance (VAD), de visualiser la décision de dialogue associée et d’exporter les résultats en JSON.

## Fonctionnalités

- Saisie d’un texte à analyser.
- Exemples de textes prêts à l’emploi.
- Affichage des scores VAD.
- Décision de dialogue basée sur des seuils.
- Export des résultats au format JSON.
- Effacement de la session.

## Lancement

Prérequis : **Python 3.10 ou plus récent**.

Depuis la racine du projet :

```bash
python -m pip install -r requirements.txt
python download_model.py
python server.py
```

Puis ouvrir :

[http://127.0.0.1:8765](http://127.0.0.1:8765)

Le premier lancement télécharge le modèle, soit environ **438 Mo**. Une fois le modèle mis en cache, l’analyse utilise les fichiers locaux et n’envoie pas le texte vers une API distante.

Le serveur écoute uniquement sur la machine locale. Il n’est pas prévu pour être exposé publiquement.

## Table de dialogue

Le projet nécessite un fichier `My_Aggregated_Logic.csv`, à placer à côté de `server.py`, avec les colonnes suivantes :

```text
Current_System_Action,User_Reaction,Next_System_Action
```

Actions prises en charge :

- `ask_clarification`
- `acknowledge`
- `offer_help`
- `respect_boundary`

Si le fichier est absent ou si aucune correspondance n’est trouvée, l’application affiche par défaut une demande de précision.

## Méthode et limites

Le modèle utilisé est [`RobroKools/vad-bert`](https://huggingface.co/RobroKools/vad-bert), prévu pour l’anglais. Il prédit trois dimensions :

- **Valence** : tonalité émotionnelle du texte.
- **Activation** : niveau d’intensité émotionnelle.
- **Dominance** : sentiment de contrôle associé au texte.

Les scores affichés sont des valeurs brutes, et non des probabilités.

Les seuils utilisés proviennent du prototype initial :

- Activation > 3.5 et dominance > 3.0 ;
- Sinon, valence < 2.5 ;
- Sinon, troisième catégorie.

Ces seuils doivent être évalués sur des données annotées avant toute utilisation réelle. Les résultats ne constituent pas un diagnostic et ne permettent pas de déterminer avec certitude l’intention ou l’état d’une personne.

L’entrée est limitée à **2 000 caractères** et le modèle à **512 tokens**. Les textes plus longs peuvent être tronqués.

## Structure du projet

```text
projet/
├── engine.py
├── server.py
├── download_model.py
├── Bert Model.py
├── test_engine.py
├── My_Aggregated_Logic.csv
├── requirements.txt
└── web/
```

- `engine.py` : validation des entrées, chargement du modèle et lecture du CSV.
- `server.py` : serveur HTTP local.
- `web/` : interface HTML, CSS et JavaScript.
- `download_model.py` : téléchargement et préparation du modèle.
- `Bert Model.py` : compatibilité avec l’appel JSON du prototype initial.
- `test_engine.py` : tests des entrées, seuils, lecture du CSV et résultats.

## Tests

Pour lancer les tests :

```bash
python -m unittest -v
```

## Modèle

Modèle utilisé : [RobroKools/vad-bert](https://huggingface.co/RobroKools/vad-bert)
