from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.security import OAuth2PasswordRequestForm
from repositories.accounts import AccountRepository
from services.auth import AuthService

router = APIRouter()

# В реальном приложении секретный ключ должен быть в конфигурации
AUTH_SERVICE = AuthService(secret_key="your-super-secret-key")

@router.post("/login")
async def login(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    account_repo: AccountRepository = Depends(lambda r: r.app.state.account_repository),
):
    account = await account_repo.get_by_login_and_password(form_data.username, form_data.password)
    if not account or account.is_blocked:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = AUTH_SERVICE.create_token(account)
    response.set_cookie(key="access_token", value=f"Bearer {token}", httponly=True)
    return {"access_token": token, "token_type": "bearer"}
