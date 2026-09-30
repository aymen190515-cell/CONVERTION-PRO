"""Bounded local file/simulation API; there is deliberately no transport opener."""
from importlib.resources import files
from fastapi import APIRouter, Depends, FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, Response
from pydantic import BaseModel
from . import chip_access as access
from convertion_pro.core.chip_workspace import Workspace, MAX_BYTES, chip_catalog

workspace = Workspace()


def local_request(request: Request):
    if (request.url.hostname not in ("127.0.0.1", "localhost", "::1")
            or request.client is None or request.client.host not in ("127.0.0.1", "::1")):
        raise HTTPException(403, "Cet espace fichier nécessite le serveur local.")
    origin = request.headers.get("origin")
    if ((origin and origin != str(request.base_url).rstrip('/'))
            or request.headers.get('sec-fetch-site') == 'cross-site'):
        raise HTTPException(403, "Requête d'une autre origine refusée.")


router = APIRouter(dependencies=[Depends(access.file_request)])


def run(operation):
    try:
        return operation()
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


async def body(request):
    chunks, size = [], 0
    async for chunk in request.stream():
        size += len(chunk)
        if size > MAX_BYTES:
            raise HTTPException(413, "Limite de 8 Mio dépassée.")
        chunks.append(chunk)
    return b''.join(chunks)


@router.get('/chips', response_class=HTMLResponse)
def page(request: Request):
    html = files('convertion_pro.ui').joinpath('chip_workspace.html').read_text(encoding='utf-8')
    remote = request.state.chip_secure
    html = html.replace('__WORKSPACE_LOCATION__',
                        'Serveur Codespaces : fichiers transmis et conservés temporairement en mémoire.'
                        if remote else 'Serveur local : fichiers conservés temporairement en mémoire.')
    if getattr(request.app.state, 'file_only', False):
        html = html.replace("Retour à l'aperçu véhicule", 'Espace fichiers uniquement')
    response = HTMLResponse(html, headers={'Cache-Control': 'no-store',
                                          'X-Frame-Options': 'DENY',
                                          'Referrer-Policy': 'no-referrer'})
    if request.state.chip_owner is None:
        response.set_cookie(access.COOKIE, access.browser_cookie(), max_age=access.TTL,
                            httponly=True, secure=remote, samesite='strict', path='/')
    return response


@router.get('/api/chips/catalog')
def catalog():
    return chip_catalog()


@router.post('/api/chips/import')
async def import_file(request: Request, profile: str = "RAW_FILE", name: str = "image.bin"):
    data = await body(request)
    return run(lambda: access.register(workspace, request.state.chip_owner,
                                        lambda: workspace.import_file(data, profile, name)))


class SimulationRequest(BaseModel):
    profile: str


@router.post('/api/chips/simulate')
def simulate(payload: SimulationRequest, request: Request):
    return run(lambda: access.register(workspace, request.state.chip_owner,
                                        lambda: workspace.simulate(payload.profile)))


@router.post('/api/chips/hardware/read', dependencies=[Depends(local_request)])
def hardware_read():
    raise HTTPException(501, "Aucun mode matériel qualifié. Aucune lecture, écriture ou commande envoyée.")


@router.get('/api/chips/sessions/{session}')
def inspect(session: str, request: Request):
    return access.owned(workspace, request.state.chip_owner, session, lambda: workspace.inspect(session))


@router.get('/api/chips/sessions/{session}/backup')
def backup(session: str, request: Request):
    data = access.owned(workspace, request.state.chip_owner, session, lambda: workspace.export_backup(session))
    return Response(data, media_type='application/zip',
                    headers={'Content-Disposition': 'attachment; filename="conversion-pro-backup.zip"',
                             'Cache-Control': 'no-store'})


@router.post('/api/chips/sessions/{session}/compare')
async def compare(session: str, request: Request):
    data = await body(request)
    return run(lambda: access.owned(workspace, request.state.chip_owner, session,
                                     lambda: workspace.compare(session, data)))


@router.delete('/api/chips/sessions/{session}')
def close(session: str, request: Request):
    return access.owned(workspace, request.state.chip_owner, session, lambda: workspace.close(session), close=True)


# Separate ASGI surface: no legacy conversion, programmer or vehicle routes.
files_app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
files_app.state.file_only = True
files_app.include_router(router)


@files_app.middleware('http')
async def no_cache(request, call_next):
    response = await call_next(request)
    response.headers['Cache-Control'] = 'no-store'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    return response


@files_app.get('/')
def files_home():
    from fastapi.responses import RedirectResponse
    return RedirectResponse('/chips')
