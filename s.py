import logging
from aiohttp import web

logging.basicConfig(level=logging.INFO)

# Route handler
async def handle_root(request):
    return web.Response(text="✅ Server is alive")

# Main entry
async def main():
    app = web.Application()
    app.add_routes([web.get("/", handle_root)])  # GET /
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8080)
    await site.start()
    logging.info("🌐 HTTP server running on port 8080")

    # Keep running forever
    import asyncio
    await asyncio.Event().wait()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
