"""
Structured error handling middleware
Produces consistent JSON error objects across the API
"""
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY, HTTP_500_INTERNAL_SERVER_ERROR
import traceback


class ErrorMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, debug: bool = False):
        super().__init__(app)
        self.debug = debug

    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except RequestValidationError as e:
            payload = {
                "code": "validation_error",
                "message": "Request validation failed",
                "details": e.errors() if self.debug else None,
            }
            return JSONResponse(status_code=HTTP_422_UNPROCESSABLE_ENTITY, content=payload)
        except Exception as e:  # pragma: no cover
            payload = {
                "code": "internal_error",
                "message": str(e) if self.debug else "Internal Server Error",
                "details": traceback.format_exc() if self.debug else None,
            }
            return JSONResponse(status_code=HTTP_500_INTERNAL_SERVER_ERROR, content=payload)
