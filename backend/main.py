import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from redis.asyncio import Redis
from fastapi_limiter import FastAPILimiter

from routes.listings.router import router as listings_router
from routes.auth.router import router as auth_router

app = FastAPI(title="Assumables API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    redis = Redis.from_url(os.environ["REDIS_URL"], encoding="utf-8", decode_responses=True)
    async def id_fn(request):
        fwd = request.headers.get("x-forwarded-for")
        return fwd.split(",")[0].strip() if fwd else request.client.host
    await FastAPILimiter.init(redis, identifier=id_fn)

app.include_router(auth_router, prefix="/api")
app.include_router(listings_router, prefix="/api")