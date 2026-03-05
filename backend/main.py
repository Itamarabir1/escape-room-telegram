# pyright: reportMissingImports=false
"""Entry point: create app, register startup, run server."""
import uvicorn

from config import config
from api.app_factory import create_app
from bootstrap import bootstrap

app = create_app()


@app.on_event("startup")
async def on_startup():
    await bootstrap(app)


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=config.PORT,
        reload=config.MODE != "production",
        timeout_keep_alive=0,
    )
