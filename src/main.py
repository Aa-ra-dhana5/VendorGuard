from fastapi import FastAPI
from src.Routes.routes import event_route
from src.Routes.admin_routes import admin_route

from src.config.logger_config import get_scheduler_logger

logger = get_scheduler_logger()


version = 'v1'

async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title='Vender',
    description='A REST API for Vendor Settlement with scheduled payout processing',
    version=version,
    lifespan=lifespan
)

app.include_router(event_route, prefix=f'/api/{version}', tags=['event'])
app.include_router(admin_route, prefix=f'/api/{version}/admin', tags=['admin'])
