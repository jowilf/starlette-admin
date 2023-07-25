from gridfs import GridFS
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp


class GridFSMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, fs: GridFS) -> None:
        super().__init__(app)
        self.fs = fs

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        request.state.fs = self.fs
        return await call_next(request)
