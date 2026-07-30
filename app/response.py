from typing import Any, Dict, Optional
from fastapi.responses import JSONResponse


def success(data: Any = None, message: str = "Success", status_code: int = 200) -> JSONResponse:
    body: Dict[str, Any] = {"success": True, "message": message}
    if data is not None:
        body["data"] = data
    return JSONResponse(content=body, status_code=status_code)


def error(message: str = "Error", status_code: int = 400, data: Any = None) -> JSONResponse:
    body: Dict[str, Any] = {"success": False, "message": message}
    if data is not None:
        body["data"] = data
    resp = JSONResponse(content=body, status_code=status_code)
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, PATCH, OPTIONS"
    resp.headers["Access-Control-Allow-Headers"] = "Authorization, Content-Type, X-API-Key"
    return resp


def not_found(message: str = "Resource not found") -> JSONResponse:
    return error(message=message, status_code=404)


def validation_error(message: str = "Validation error", data: Any = None) -> JSONResponse:
    return error(message=message, status_code=422, data=data)
