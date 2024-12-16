import jwt
from fastapi import Depends, WebSocketException, status
from fastapi.exceptions import HTTPException
from fastapi.requests import Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette.websockets import WebSocket

from app.utils.auth import get_user



class JWTBearer(HTTPBearer):

    def __init__(self, auto_error: bool = True):

        super(JWTBearer, self).__init__(auto_error=auto_error)

    async def __call__(self, request: Request):
        """
        Validate the incoming request for JWT authentication.
        """
        credentials: HTTPAuthorizationCredentials = await super(
            JWTBearer, self
        ).__call__(request)

        if credentials:
            if not credentials.scheme == "Bearer":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Invalid authentication scheme.",
                )

            await get_user(credentials.credentials)
            try:
                payload = jwt.decode(
                    credentials.credentials, options={"verify_signature": False}
                )
                return payload
            except jwt.ExpiredSignatureError:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has expired.",
                )
            except jwt.DecodeError:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token."
                )

        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid authorization code.",
            )


class AdminJWTBearer:

    async def __call__(self, user_dict: dict = Depends(JWTBearer())):
        if user_dict.get("user_type") != "Admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only Admin users are allowed to access.",
            )
        return user_dict


class BuyerRoleDependency:

    async def __call__(self, user_info: dict = Depends(JWTBearer())):
        user_type = user_info.get("user_type")
        if user_type == "Buyer":
            return user_info
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only buyers are allowed to access this resource.",
            )


class SellerRoleDependency:

    async def __call__(self, user_info: dict = Depends(JWTBearer())):
        user_type = user_info.get("user_type")
        if user_type == "Seller":
            return user_info
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only sellers are allowed to access this resource.",
            )


class WebSocketJWTBearer:
    async def __call__(self, websocket: WebSocket):
        """
        Validates the WebSocket connection for JWT authentication.
        """
        auth_header = websocket.query_params.get("Authorization")
        if auth_header is None:
            raise WebSocketException(
                code=status.WS_1008_POLICY_VIOLATION, reason="Auth header is empty"
            )

        scheme, _, token = auth_header.partition(" ")
        if scheme.lower() != "bearer" or not token:
            raise WebSocketException(
                code=status.WS_1008_POLICY_VIOLATION, reason="Incorrect auth type"
            )

        try:
            await get_user(token)

            payload = jwt.decode(token, options={"verify_signature": False})
        except HTTPException:
            raise WebSocketException(
                code=status.WS_1008_POLICY_VIOLATION,
                reason="Could not retrieve user information",
            )

        except Exception as e:
            raise WebSocketException(
                code=status.WS_1008_POLICY_VIOLATION,
                reason="Could not retrieve user information",
            )

        return payload


