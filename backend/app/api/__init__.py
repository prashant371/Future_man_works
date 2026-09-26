from app.api.auth import router as auth_router
from app.api.chat import router as chat_router
from app.api.connections import router as connections_router
from app.api.tasks import router as tasks_router

__all__ = ["auth_router", "chat_router", "connections_router", "tasks_router"]
