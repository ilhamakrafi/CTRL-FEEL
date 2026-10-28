import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit
from engine import Analyzer

ROOT = Path(__file__).resolve().parent
analyzer = Analyzer(ROOT)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_args):
        pass

    def send(self, status, payload, content_type='application/json; charset=utf-8'):
        data = json.dumps(payload, ensure_ascii=False).encode() if isinstance(payload, dict) else payload
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'")
        self.end_headers()
        self.wfile.write(data)

    def allowed(self):
        return self.headers.get('Host', '') in {'127.0.0.1:8765', 'localhost:8765'}

    def do_GET(self):
        if not self.allowed():
            return self.send(403, {'error': 'Hôte non autorisé.'})
        files = {'/': ('index.html', 'text/html; charset=utf-8'), '/app.js': ('app.js', 'text/javascript; charset=utf-8'), '/style.css': ('style.css', 'text/css; charset=utf-8')}
        path = urlsplit(self.path).path
        if path == '/api/status':
            return self.send(200, {'model': 'RobroKools/vad-bert', 'csv_available': (ROOT / 'My_Aggregated_Logic.csv').is_file()})
        if path not in files:
            return self.send(404, {'error': 'Ressource introuvable.'})
        name, mime = files[path]
        self.send(200, (ROOT / 'web' / name).read_bytes(), mime)

    def do_POST(self):
        origin = self.headers.get('Origin')
        if not self.allowed() or origin not in {None, 'http://127.0.0.1:8765', 'http://localhost:8765'}:
            return self.send(403, {'error': 'Origine non autorisée.'})
        if self.path != '/api/analyze':
            return self.send(404, {'error': 'Ressource introuvable.'})
        if self.headers.get_content_type() != 'application/json':
            return self.send(415, {'error': 'Le contenu doit être au format JSON.'})
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 < length <= 16000:
                return self.send(413, {'error': 'Requête vide ou trop volumineuse.'})
            data = json.loads(self.rfile.read(length))
            result = analyzer.analyze(data)
            return self.send(200, result)
        except (ValueError, UnicodeDecodeError) as exc:
            return self.send(400, {'error': str(exc)})
        except RuntimeError as exc:
            return self.send(503, {'error': str(exc)})
        except Exception:
            return self.send(500, {'error': 'L’analyse a échoué. Vérifiez le modèle et la table CSV.'})


if __name__ == '__main__':
    print('CTRL+FEEL : http://127.0.0.1:8765 — Ctrl+C pour arrêter', flush=True)
    try:
        ThreadingHTTPServer(('127.0.0.1', 8765), Handler).serve_forever()
    except KeyboardInterrupt:
        pass
