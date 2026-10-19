from fastapi import APIRouter, Request, Response

from solar_sites.config import Settings
from solar_sites.modules.auth import service
from solar_sites.modules.auth.authentication import COOKIE_NAME
from solar_sites.modules.auth.dependencies import IdentityDep, PasswordsDep
from solar_sites.modules.auth.schemas import Credentials, MeOutput, SessionOutput
from solar_sites.modules.auth.service import NewSession
from solar_sites.platform.dependencies import SessionDep, SettingsDep

router = APIRouter(prefix="/api", tags=["auth"])


def _set_cookie(
    response: Response,
    request: Request,
    session: NewSession,
    settings: Settings,
) -> None:
    response.set_cookie(
        COOKIE_NAME,
        session.token,
        httponly=True,
        samesite="lax",
        path="/",
        secure=settings.cookie_secure or request.url.scheme == "https",
        max_age=settings.session_age_seconds,
    )


@router.post("/register", status_code=201, response_model=SessionOutput, operation_id="register")
async def register(
    body: Credentials,
    response: Response,
    request: Request,
    db: SessionDep,
    passwords: PasswordsDep,
    settings: SettingsDep,
) -> SessionOutput:
    session = await service.register(
        db,
        passwords=passwords,
        session_age=settings.session_age_seconds,
        email=str(body.email),
        password=body.password,
        previous_token=request.cookies.get(COOKIE_NAME),
    )
    _set_cookie(response, request, session, settings)
    return SessionOutput(csrf_token=session.csrf_token)


@router.post("/login", response_model=SessionOutput, operation_id="login")
async def login(
    body: Credentials,
    response: Response,
    request: Request,
    db: SessionDep,
    passwords: PasswordsDep,
    settings: SettingsDep,
) -> SessionOutput:
    session = await service.login(
        db,
        passwords=passwords,
        session_age=settings.session_age_seconds,
        email=str(body.email),
        password=body.password,
        previous_token=request.cookies.get(COOKIE_NAME),
    )
    _set_cookie(response, request, session, settings)
    return SessionOutput(csrf_token=session.csrf_token)


@router.post("/logout", status_code=204, operation_id="logout")
async def logout(
    response: Response,
    request: Request,
    current_identity: IdentityDep,
    db: SessionDep,
    settings: SettingsDep,
) -> None:
    await service.logout(db, identity=current_identity)
    response.delete_cookie(
        COOKIE_NAME,
        path="/",
        httponly=True,
        samesite="lax",
        secure=settings.cookie_secure or request.url.scheme == "https",
    )


@router.get("/me", response_model=MeOutput, operation_id="me")
async def me(current_identity: IdentityDep) -> MeOutput:
    return MeOutput(
        email=current_identity.email,
        csrf_token=current_identity.csrf_token,
    )
