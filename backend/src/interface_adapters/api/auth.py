from datetime import timedelta
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from src.infrastructure.db.models import UserModel
from src.infrastructure.security.password import PasswordHasher
from src.infrastructure.security.jwt import JWTHandler, InvalidTokenError
from src.infrastructure.config import settings

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])
security = HTTPBearer()


class LoginRequest(BaseModel):
    """ログインリクエスト"""

    username: str
    password: str


class TokenResponse(BaseModel):
    """トークンレスポンス"""

    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    """ユーザー情報レスポンス"""

    uuid: str
    username: str
    email: str
    is_active: bool


jwt_handler = JWTHandler(secret_key=settings.SECRET_KEY, algorithm=settings.ALGORITHM)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> UserModel:
    """
    JWTトークンから現在のユーザーを取得する依存関数

    Args:
        credentials: HTTPベアラートークン

    Returns:
        UserModel: 認証されたユーザー

    Raises:
        HTTPException: 認証失敗時
    """
    token = credentials.credentials

    try:
        user_uuid = jwt_handler.verify_token(token)
    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = await UserModel.filter(uuid=user_uuid, is_active=True).first()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """
    ユーザーログイン

    Args:
        request: ログインリクエスト（ユーザー名とパスワード）

    Returns:
        TokenResponse: アクセストークン

    Raises:
        HTTPException: 認証失敗時
    """
    # ユーザーを検索
    user = await UserModel.filter(username=request.username).first()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )

    # パスワード検証
    if not PasswordHasher.verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )

    # アクティブチェック
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive",
        )

    # トークン生成
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = jwt_handler.create_access_token(
        user_uuid=str(user.uuid), expires_delta=access_token_expires
    )

    return TokenResponse(access_token=access_token)


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: UserModel = Depends(get_current_user)):
    """
    現在のユーザー情報を取得

    Args:
        current_user: 認証済みユーザー（依存注入）

    Returns:
        UserResponse: ユーザー情報
    """
    return UserResponse(
        uuid=str(current_user.uuid),
        username=current_user.username,
        email=current_user.email,
        is_active=current_user.is_active,
    )
