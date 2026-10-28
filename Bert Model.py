import json
from pathlib import Path
from engine import Analyzer

analyzer = Analyzer(Path(__file__).resolve().parent)


def process_json_request(json_payload):
    try:
        return json.dumps(analyzer.analyze(json.loads(json_payload)), ensure_ascii=False, indent=2)
    except (ValueError, RuntimeError) as exc:
        return json.dumps({'error': str(exc)}, ensure_ascii=False)


if __name__ == '__main__':
    print('Lancez python server.py pour utiliser l’interface web.')
