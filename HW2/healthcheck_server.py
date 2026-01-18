from aiohttp import web
import asyncio

async def healthcheck(request):
    return web.Response(text="OK")

async def start_healthcheck_server():
    app = web.Application()
    app.router.add_get('/health', healthcheck)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 10000)
    await site.start()

async def run_healthcheck():
    await start_healthcheck_server()
    while True:
        await asyncio.sleep(3600)
