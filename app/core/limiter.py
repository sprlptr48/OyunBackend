from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.requests import Request


def get_request_identifier(request: Request) -> str:
    if hasattr(request.state, "user") and request.state.user:
        return str(request.state.user.id)
    else:
        return get_remote_address(request)


limiter = Limiter(key_func=get_request_identifier, default_limits=["15/minute"])
