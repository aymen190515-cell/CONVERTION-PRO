"""Explicit file-only proxy policy and bounded browser ownership. No device access."""
import hashlib
import hmac
import os
import re
import secrets
import time
from threading import RLock

from fastapi import HTTPException, Request, Response

COOKIE = 'cp_chip_browser'
TTL = 8 * 60 * 60
SECRET = secrets.token_bytes(32)  # Process lifetime; never persisted or logged.
lock = RLock()
owners = {}  # At most Workspace.MAX_SESSIONS entries, protected by lock.


def configured_origin():
    value = os.environ.get('CP_FILE_ORIGIN', '')
    if value and not re.fullmatch(r'https://[a-z0-9]+(?:-[a-z0-9]+)*-[0-9]+\.app\.github\.dev', value):
        raise HTTPException(503, 'CP_FILE_ORIGIN doit être une origine HTTPS Codespaces exacte, sans chemin.')
    return value


def file_request(request: Request, response: Response):
    # Actual loopback peer only: the file-only launcher disables proxy_headers.
    # Never derive authorization from X-Forwarded-Host/For/Proto or a wildcard.
    if request.client is None or request.client.host not in ('127.0.0.1', '::1'):
        raise HTTPException(403, 'Connexion locale du proxy requise.')
    host = request.headers.get('host', '')
    remote = configured_origin() if getattr(request.app.state, 'file_only', False) else ''
    if remote:
        if host != remote.removeprefix('https://'):
            raise HTTPException(403, 'Hôte du workspace non autorisé.')
        expected = remote
    else:
        if request.url.hostname not in ('127.0.0.1', 'localhost', '::1'):
            raise HTTPException(403, 'Cet espace fichier nécessite le serveur local.')
        expected = str(request.base_url).rstrip('/')
    origin = request.headers.get('origin')
    # A user may open the page from the Ports tab. This GET contains no file data.
    page_navigation = (request.method == 'GET' and request.url.path == '/chips'
                       and request.headers.get('sec-fetch-mode') == 'navigate'
                       and request.headers.get('sec-fetch-dest') == 'document'
                       and origin is None)
    if ((origin is not None and origin != expected)
            or (request.headers.get('sec-fetch-site') == 'cross-site' and not page_navigation)):
        raise HTTPException(403, "Requête d'une autre origine refusée.")
    if request.method not in ('GET', 'HEAD', 'OPTIONS'):
        if request.headers.get('x-chip-workspace') != '1' or (remote and origin != expected):
            raise HTTPException(403, 'En-tête workspace et origine attendus.')
    request.state.chip_secure = bool(remote)
    response.headers['Cache-Control'] = 'no-store'
    request.state.chip_owner = valid_cookie(request.cookies.get(COOKIE, ''))
    if request.url.path != '/chips' and request.state.chip_owner is None:
        raise HTTPException(403, "Ouvrir /chips pour initialiser une session navigateur.")


def valid_cookie(value):
    try:
        nonce, issued, signature = value.split('.')
        payload = f'{nonce}.{issued}'
        if (len(nonce) != 64 or not 0 <= time.time() - int(issued) < TTL
                or not hmac.compare_digest(signature, hmac.new(SECRET, payload.encode(), hashlib.sha256).hexdigest())):
            return None
        return value
    except (ValueError, TypeError):
        return None


def browser_cookie():
    payload = f'{secrets.token_hex(32)}.{int(time.time())}'
    return payload + '.' + hmac.new(SECRET, payload.encode(), hashlib.sha256).hexdigest()


def prune(workspace):
    for session, (owner, expiry) in list(owners.items()):
        if expiry <= time.time():
            try:
                workspace.close(session)
            except ValueError:
                pass
            del owners[session]


def register(workspace, owner, operation):
    with lock:
        prune(workspace)
        result = operation()
        owners[result['id']] = (owner, int(owner.split('.')[1]) + TTL)
        return result


def owned(workspace, owner, session, operation, close=False):
    with lock:
        prune(workspace)
        record = owners.get(session)
        if record is None or not hmac.compare_digest(record[0], owner):
            # Same response for another browser's snapshot and a nonexistent ID.
            raise HTTPException(404, 'Session inconnue ou expirée pour ce navigateur.')
        result = operation()
        if close:
            del owners[session]
        return result
