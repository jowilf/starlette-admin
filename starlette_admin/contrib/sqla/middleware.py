from contextlib import contextmanager
from typing import Generator

from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp


class DBSessionMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, engine: Engine) -> None:
        super().__init__(app)
        self.engine = engine

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        with get_session(self.engine) as session:
            request.state.session = session
            response = await call_next(request)
            return response


@contextmanager
def get_session(engine: Engine) -> Generator[Session, None, None]:
    session: Session = Session(engine)
    try:
        yield session
    except Exception as e:  # pragma: no cover
        session.rollback()
        raise e
    finally:
        session.close()
