from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBearer

from app.auth.router import router as auth_router
from app.config import settings
from app.graphql.schema import graphql_app

app = FastAPI(
    title=settings.app_name,
    swagger_ui_parameters={"persistAuthorization": True}
)

# Включаем авторизацию в Swagger
security = HTTPBearer()

app.include_router(auth_router)
app.mount("/graphql", graphql_app)
app.mount("/admin", StaticFiles(directory="app/static", html=True), name="admin")


@app.get("/")
def root():
    return {"app": settings.app_name, "environment": settings.environment}