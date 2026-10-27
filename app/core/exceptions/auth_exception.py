# app/core/exceptions/auth_exception.py
from fastapi import HTTPException


class AuthException(HTTPException):
    def __init__(self, status_code: int, message: str):
        super().__init__(status_code=status_code, detail=message)