from fastapi import APIRouter, HTTPException, Response, Request
from pydantic import BaseModel
import hmac
from itsdangerous import TimestampSigner, BadSignature, SignatureExpired
from config import settings

router = APIRouter(prefix="/auth", tags=["auth"])

COOKIE_NAME = settings.COOKIE_NAME.get_secret_value()
signer = TimestampSigner(settings.APP_SESSION_SECRET.get_secret_value())

class LoginIn(BaseModel):
    token: str

@router.post("/login")
async def login(payload: LoginIn, response: Response):
    expected = settings.APP_ACCESS_TOKEN.get_secret_value()
    if not hmac.compare_digest(expected, payload.token):
        raise HTTPException(status_code=401, detail="Invalid token")

    value = signer.sign(b"ok").decode()
    response.set_cookie(
        COOKIE_NAME,
        value,
        max_age=settings.APP_SESSION_MAX_AGE,
        httponly=True,
        samesite="lax",
        secure=False,
        path="/"
    )
    return {"ok": True}

def require_auth(request: Request):
    raw = request.cookies.get(COOKIE_NAME)
    if not raw:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        signer.unsign(raw, max_age=settings.APP_SESSION_MAX_AGE)
    except (BadSignature, SignatureExpired):
        raise HTTPException(status_code=401, detail="Not authenticated")

@router.get("/me")
async def me(request: Request):
    require_auth(request)
    return {"ok": True}

@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie(COOKIE_NAME, path="/")
    return {"ok": True}