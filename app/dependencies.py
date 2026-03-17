from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from services.auth import AuthService
from repositories.accounts import AccountRepository
from models.schemas import Account

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login", auto_error=False)

# В реальном приложении секретный ключ должен быть в конфигурации
AUTH_SERVICE = AuthService(secret_key="your-super-secret-key")

async def get_current_account(
    request: Request,
    token: str = Depends(oauth2_scheme)
) -> Account:
    if token is None:
        # Попробуем получить токен из cookie, если его нет в заголовке
        token = request.cookies.get("access_token")
        if token and token.startswith("Bearer "):
            token = token.split("Bearer ")[1]

    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = AUTH_SERVICE.verify_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    account_id = int(payload.get("sub"))
    account_repo: AccountRepository = request.app.state.account_repository
    account = await account_repo.get_by_id(account_id)
    
    if account is None or account.is_blocked:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return account
