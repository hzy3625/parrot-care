import sys
sys.path.insert(0, '.')
from main import app

routes = []
for r in app.routes:
    path = getattr(r, 'path', getattr(r, 'url_path', None)) or str(r)
    methods = getattr(r, 'methods', None)
    routes.append((path, methods))
print(f'Total routes: {len(routes)}')
for path, methods in routes:
    m = ','.join(sorted(methods)) if methods else '-'
    print(f'  [{m}] {path}')

# Test health endpoint
import asyncio
from httpx import AsyncClient, ASGITransport

async def test_health():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url='http://test') as ac:
        resp = await ac.get('/health')
        print(f'\nHealth check: {resp.status_code}')
        print(f'Response: {resp.json()}')

asyncio.run(test_health())
