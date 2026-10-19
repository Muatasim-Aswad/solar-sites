from typing import Annotated, cast

from fastapi import Depends, Header, Request
from fastapi.security import APIKeyCookie

from solar_sites.modules.auth.authentication import COOKIE_NAME, authenticate_request
from solar_sites.modules.auth.passwords import Passwords
from solar_sites.modules.auth.service import Identity
from solar_sites.platform.dependencies import SessionDep

# session
session_cookie = APIKeyCookie(name=COOKIE_NAME, auto_error=False)


# passwords
def get_passwords(request: Request) -> Passwords:
    return cast(Passwords, request.app.state.passwords)


PasswordsDep = Annotated[Passwords, Depends(get_passwords)]


# identity
async def get_current_identity(
    request: Request,
    db: SessionDep,
    token: Annotated[str | None, Depends(session_cookie)],
    csrf_token: Annotated[str | None, Header(alias="X-CSRF-Token")] = None,
) -> Identity:
    return await authenticate_request(
        request=request,
        db=db,
        token=token,
        csrf_token=csrf_token,
    )


IdentityDep = Annotated[Identity, Depends(get_current_identity)]
