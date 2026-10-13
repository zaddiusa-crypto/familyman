from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
import time
import logging

from app.core.config import settings
from app.core.database import init_db, close_db, AsyncSessionLocal
from app.core.exceptions import AppException
from app.core.models import Base
from app.modules.auth.router import router as auth_router
from app.modules.users.router import router as users_router
from app.modules.applications.router import router as applications_router
from app.modules.chat.router import router as chat_router
from app.modules.notifications.router import router as notifications_router
from app.modules.announcements.router import router as announcements_router
from app.modules.payments.router import router as payments_router
from app.modules.admin.router import router as admin_router
from app.modules.lodges.router import router as lodges_router
from app.modules.media.router import router as media_router
from app.ws.socketio_app import socketio_app

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up...")
    await init_db()
    logger.info("Database initialized")
    yield
    logger.info("Shutting down...")
    await close_db()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="FamilyMan API - Multi-tenant Lodge Management System",
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


@app.middleware("http")
async def tenant_context_middleware(request: Request, call_next):
    lodge_id = request.headers.get("X-Lodge-ID")
    if lodge_id:
        async with AsyncSessionLocal() as session:
            await session.execute(text(f"SET LOCAL app.current_lodge_id = '{lodge_id}'"))
            await session.commit()
    response = await call_next(request)
    return response


@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "error_code": exc.error_code},
        headers=exc.headers,
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    import traceback
    traceback.print_exc()
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error_code": "INTERNAL_ERROR"},
    )


@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": settings.APP_VERSION}


app.mount("/ws", socketio_app)

app.include_router(auth_router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(users_router, prefix="/api/v1/users", tags=["Users"])
app.include_router(applications_router, prefix="/api/v1/applications", tags=["Applications"])
app.include_router(chat_router, prefix="/api/v1/chats", tags=["Chats"])
app.include_router(notifications_router, prefix="/api/v1/notifications", tags=["Notifications"])
app.include_router(announcements_router, prefix="/api/v1/announcements", tags=["Announcements"])
app.include_router(payments_router, prefix="/api/v1/payments", tags=["Payments"])
app.include_router(admin_router, prefix="/api/v1/admin", tags=["Admin"])
app.include_router(lodges_router, prefix="/api/v1/lodges", tags=["Lodges"])
app.include_router(media_router, prefix="/api/v1/media", tags=["Media"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=settings.DEBUG)