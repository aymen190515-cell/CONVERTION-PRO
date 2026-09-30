"""Proxy reproduction and file-only isolation: synthetic bytes, no hardware."""
from io import BytesIO
from zipfile import ZipFile

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from convertion_pro.core.chip_workspace import Workspace
from convertion_pro.ui import chip_api, chip_access

ORIGIN = 'https://literate-bassoon-jr444r9q554p3qwrv-8000.app.github.dev'
HOST = ORIGIN.removeprefix('https://')


@pytest.fixture(autouse=True)
def reset(monkeypatch):
    monkeypatch.setenv('CP_FILE_ORIGIN', ORIGIN)
    monkeypatch.setattr(chip_api, 'workspace', Workspace())
    monkeypatch.setattr(chip_access, 'owners', {})


def browser(app=chip_api.files_app, peer='127.0.0.1'):
    # HTTPS browser URL but plain HTTP ASGI hop: TLS terminates at the proxy.
    async def proxy(scope, receive, send):
        scope = dict(scope, scheme='http')
        await app(scope, receive, send)
    client = TestClient(proxy, base_url=ORIGIN, client=(peer, 40000))
    client.headers.update({'Origin': ORIGIN, 'X-Chip-Workspace': '1',
                           'Sec-Fetch-Site': 'same-origin'})
    return client


def test_original_preview_stays_local_even_with_configured_origin():
    app = FastAPI()
    app.include_router(chip_api.router)
    with browser(app) as c:
        r = c.get('/chips')
        assert r.status_code == 403
        assert 'serveur local' in r.json()['detail']


def test_codespaces_file_round_trip_and_safe_surface():
    with browser() as c:
        page = c.get('/chips')
        assert page.status_code == 200
        assert 'Serveur Codespaces' in page.text
        assert '__WORKSPACE_LOCATION__' not in page.text
        cookie = page.headers['set-cookie']
        for flag in ('HttpOnly', 'SameSite=strict', 'Secure', 'Max-Age=28800'):
            assert flag in cookie
        assert 'Domain=' not in cookie
        assert c.get('/api/chips/catalog').status_code == 200
        data = bytes(range(256)) * 16
        r = c.post('/api/chips/import?profile=ST_M24C32', content=data)
        assert r.status_code == 200
        assert r.json()['source'] == 'FILE' and not r.json()['hardware_access']
        sid = r.json()['id']
        url = '/api/chips/sessions/' + sid
        assert c.get(url).status_code == 200
        backup = c.get(url + '/backup')
        assert backup.headers['cache-control'] == 'no-store'
        with ZipFile(BytesIO(backup.content)) as z:
            assert z.read('memory.bin') == data
        result = c.post(url + '/compare', content=data).json()
        assert result['identical'] and not result['hardware_verified']
        assert c.post(url + '/compare', content=data[:-1]).json()['changed_byte_count'] == 1
        sim = c.post('/api/chips/simulate', json={'profile':'ST_M24C32'})
        assert sim.json()['source'] == 'SIMULATED'
        assert c.delete(url).status_code == 200
        assert c.get(url).status_code == 404
        assert c.post('/api/chips/hardware/read').status_code == 403
        for path in ('/api/convert', '/api/read-memory', '/api/chips/hardware/write',
                     '/api/chips/hardware/erase', '/api/chips/hardware/unlock'):
            assert c.post(path).status_code == 404


def test_browser_ownership_even_when_snapshot_id_is_known():
    with browser() as a, browser() as b:
        a.get('/chips'); b.get('/chips')
        assert a.cookies[chip_access.COOKIE] != b.cookies[chip_access.COOKIE]
        sid = a.post('/api/chips/import', content=b'private synthetic bytes').json()['id']
        url = '/api/chips/sessions/' + sid
        for method, suffix, kwargs in [('get','',{}), ('get','/backup',{}),
                                      ('post','/compare',{'content': b'x'}), ('delete','',{})]:
            assert getattr(b, method)(url + suffix, **kwargs).status_code == 404
        assert a.get(url).status_code == 200
        assert a.get('/chips').headers.get('set-cookie') is None
        assert a.get(url).status_code == 200


@pytest.mark.parametrize('headers', [
    {'Origin':'https://attacker.example'}, {'Origin':'null'},
    {'Origin':'https://other-8000.app.github.dev'},
    {'Host':'other-8000.app.github.dev'}, {'Host':HOST+'.attacker.example'},
    {'Host':'127.0.0.1', 'X-Forwarded-Host':HOST},
    {'Sec-Fetch-Site':'cross-site'}, {'X-Chip-Workspace':'0'},
])
def test_bad_origin_host_and_csrf_blocked(headers):
    with browser() as c:
        c.get('/chips')
        assert c.post('/api/chips/import', content=b'x', headers=headers).status_code == 403
        assert not chip_access.owners


def test_missing_origin_or_cookie_and_tampering_refused():
    with browser() as c:
        assert c.post('/api/chips/import', content=b'x').status_code == 403
        c.get('/chips')
        c.headers.pop('origin')
        assert c.post('/api/chips/import', content=b'x').status_code == 403
        c.headers['Origin'] = ORIGIN
        c.cookies.clear()
        c.cookies.set(chip_access.COOKIE, 'fabricated.123.fake')
        assert c.post('/api/chips/import', content=b'x').status_code == 403


def test_non_loopback_peer_cannot_claim_to_be_proxy():
    with browser(peer='192.0.2.1') as c:
        assert c.get('/chips', headers={'X-Forwarded-For':'127.0.0.1'}).status_code == 403


def test_ports_tab_can_navigate_to_page_but_not_read_snapshots_cross_site():
    with browser() as c:
        c.headers.pop('origin')
        headers = {'Sec-Fetch-Site':'cross-site', 'Sec-Fetch-Mode':'navigate',
                   'Sec-Fetch-Dest':'document'}
        assert c.get('/chips', headers=headers).status_code == 200
        assert c.get('/api/chips/catalog', headers=headers).status_code == 403
        assert c.get('/chips', headers={**headers, 'Sec-Fetch-Dest':'iframe'}).status_code == 403


def test_proxy_header_misconfiguration_fails_closed():
    app = ProxyHeadersMiddleware(chip_api.files_app, trusted_hosts=['127.0.0.1'])
    with browser(app) as c:
        assert c.get('/chips', headers={'X-Forwarded-For':'192.0.2.2'}).status_code == 403


@pytest.mark.parametrize('value', ['', 'https://*.app.github.dev', ORIGIN+'/chips',
                                  'http://'+HOST, 'https://attacker.example'])
def test_opt_in_is_exact_and_required(value, monkeypatch):
    monkeypatch.setenv('CP_FILE_ORIGIN', value)
    with browser() as c:
        assert c.get('/chips').status_code in (403, 503)


def test_expired_cookie_releases_snapshot_on_next_session_operation(monkeypatch):
    now = chip_access.time.time()
    monkeypatch.setattr(chip_access.time, 'time', lambda: now)
    with browser() as c:
        c.get('/chips')
        sid = c.post('/api/chips/import', content=b'x').json()['id']
        monkeypatch.setattr(chip_access.time, 'time', lambda: now + chip_access.TTL + 1)
        assert c.get('/api/chips/sessions/'+sid).status_code == 403
        c.get('/chips')
        assert c.post('/api/chips/import', content=b'y').status_code == 200
        assert sid not in chip_access.owners
        with pytest.raises(ValueError):
            chip_api.workspace.inspect(sid)


def test_budgets_are_shared_between_browsers(monkeypatch):
    from convertion_pro.core import chip_workspace
    monkeypatch.setattr(chip_workspace, 'MAX_STORED_BYTES', 3)
    with browser() as a, browser() as b:
        a.get('/chips'); b.get('/chips')
        sid = a.post('/api/chips/import', content=b'abc').json()['id']
        assert b.post('/api/chips/import', content=b'x').status_code == 422
        assert a.delete('/api/chips/sessions/'+sid).status_code == 200
        assert b.post('/api/chips/import', content=b'x').status_code == 200


def test_documented_launcher_selects_only_files_and_disables_proxy_headers(monkeypatch):
    import runpy
    from pathlib import Path
    import uvicorn
    calls = []
    monkeypatch.setattr(uvicorn, 'run', lambda *args, **kwargs: calls.append((args, kwargs)))
    runpy.run_path(str(Path(__file__).parents[1] / 'preview.py'), run_name='__main__')
    assert len(calls) == 1
    assert calls[0] == ((chip_api.files_app,), {'host':'127.0.0.1', 'port':8000, 'proxy_headers':False})
