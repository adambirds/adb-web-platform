import logging
import os
import shutil
import tempfile
from pathlib import Path

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

# These imports execute the patching and make the middleware available.
# The 'noqa' comment prevents linters from flagging them as unused.
import app.asgi_handler_logging  # noqa: F401
from app.asgi_middleware import GraphQL400LoggerMiddleware

logger = logging.getLogger(__name__)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "app.settings")

# Get the default Django ASGI application and wrap it with our logging middleware.
django_asgi_app: GraphQL400LoggerMiddleware = GraphQL400LoggerMiddleware(get_asgi_application())

# The main application router. It directs traffic based on protocol type.
application: ProtocolTypeRouter = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": None,  # Placeholder, will be replaced in lazy_setup()
    }
)


def get_websocket_router() -> AuthMiddlewareStack:
    """
    Creates and returns the WebSocket routing configuration.
    This is isolated in a function to avoid import issues during application startup.
    """

    return AuthMiddlewareStack(
        URLRouter(
            [
                # WebSocket routes go here
            ]
        )
    )


def lazy_setup() -> None:
    """
    Performs setup that should only run once the Django app is initialized.
    This includes setting up WebSocket routing and, in development, serving
    static and media files.
    """
    from django.conf import settings

    # Always configure the WebSocket router.
    application.application_mapping["websocket"] = get_websocket_router()

    if not settings.DEBUG:
        logger.info("⚙️ Production mode: skipping static/media mounting")
        return

    logger.info("🛠 Development mode: mounting static and media files via Starlette")

    from django.contrib.staticfiles import finders
    from starlette.applications import Starlette
    from starlette.routing import Mount, Route
    from starlette.staticfiles import StaticFiles

    # Create a temporary directory to collect static files for development serving.
    static_root_dev = Path(tempfile.gettempdir()) / "app-dev-static"
    if static_root_dev.exists():
        shutil.rmtree(static_root_dev)
    static_root_dev.mkdir(parents=True)

    # Collect static files from all finders into the temporary directory.
    # Renamed 'path' to 'static_file_path' to avoid shadowing the URL 'path' import.
    for finder in finders.get_finders():
        for static_file_path, storage in finder.list([]):
            source_path: str = storage.path(static_file_path)
            target_path: Path = static_root_dev / static_file_path
            target_path.parent.mkdir(parents=True, exist_ok=True)
            if not target_path.exists():
                shutil.copy2(source_path, target_path)

    logger.info("✅ Merged static files into: %s", static_root_dev)

    # Define routes for serving static, media, and the main Django app.
    routes: list[Route | Mount] = [
        Mount("/static", StaticFiles(directory=static_root_dev), name="static"),
        Mount("/media", StaticFiles(directory=settings.MEDIA_ROOT), name="media"),
        Mount("/", app=django_asgi_app),
    ]

    # Create a Starlette application to handle HTTP requests in development.
    http_app = Starlette(routes=routes)

    # Replace the default http handler with the new Starlette app.
    application.application_mapping["http"] = http_app


# Run the lazy setup to finalize the application configuration.
lazy_setup()
