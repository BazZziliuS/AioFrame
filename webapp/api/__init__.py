from fastapi import APIRouter

from webapp.api.routes import admin, captcha, feedback, me

api_router = APIRouter(prefix="/api")
api_router.include_router(me.router)
api_router.include_router(captcha.router)
api_router.include_router(feedback.router)
api_router.include_router(admin.router)
