"""
Connections API Routes

POST /api/connections/github/auth     — Get GitHub OAuth URL
POST /api/connections/github/callback — Handle OAuth callback & save token
GET  /api/connections                 — List user's connected platforms
DELETE /api/connections/{platform}    — Disconnect a platform
"""

import httpx
import jwt
from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database.database import get_db
from app.database.models import User, PlatformConnection
from app.auth.security import get_current_user

router = APIRouter(prefix="/api/connections", tags=["Connections"])
settings = get_settings()


class PlatformResponse(BaseModel):
    platform: str
    name: str
    description: str
    icon: str
    connected: bool
    available: bool


class AuthUrlResponse(BaseModel):
    url: str

class CallbackRequest(BaseModel):
    code: str
    state: str


@router.get("", response_model=list[PlatformResponse])
async def list_connections(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all available platforms and the user's connection status."""
    platforms_def = [
        {"id": "github", "name": "GitHub", "desc": "Manage repos, issues, and PRs", "icon": "github", "available": True},
        {"id": "linkedin", "name": "LinkedIn", "desc": "Draft and publish posts", "icon": "linkedin", "available": False},
        {"id": "mail", "name": "Gmail", "desc": "Read and send emails", "icon": "mail", "available": False},
        {"id": "calendar", "name": "Google Calendar", "desc": "Manage schedule", "icon": "calendar", "available": False},
    ]

    result = await db.execute(
        select(PlatformConnection).where(PlatformConnection.user_id == current_user.id)
    )
    connections = {c.platform: c for c in result.scalars().all()}

    response = []
    for p in platforms_def:
        connected = p["id"] in connections
        response.append(
            PlatformResponse(
                platform=p["id"],
                name=p["name"],
                description=p["desc"],
                icon=p["icon"],
                connected=connected,
                available=p["available"],
            )
        )
    return response


@router.post("/github/auth", response_model=AuthUrlResponse)
async def github_auth_url(current_user: User = Depends(get_current_user)):
    """Generate the GitHub OAuth URL."""
    if not settings.GITHUB_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="GitHub OAuth is not configured on the server.",
        )
    
    # Generate CSRF state token
    expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    state = jwt.encode(
        {"sub": str(current_user.id), "exp": expire},
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    
    scopes = "repo,user"
    url = f"https://github.com/login/oauth/authorize?client_id={settings.GITHUB_CLIENT_ID}&redirect_uri={settings.GITHUB_REDIRECT_URI}&scope={scopes}&state={state}"
    return AuthUrlResponse(url=url)


@router.post("/github/callback")
async def github_callback(
    request: CallbackRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Exchange the OAuth code for an access token and save it."""
    # Validate OAuth State CSRF
    try:
        payload = jwt.decode(request.state, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("sub") != str(current_user.id):
            raise HTTPException(status_code=400, detail="Invalid OAuth state.")
    except jwt.PyJWTError:
        raise HTTPException(status_code=400, detail="Invalid or expired OAuth state.")

    async with httpx.AsyncClient() as client:
        # Exchange code for token
        response = await client.post(
            "https://github.com/login/oauth/access_token",
            headers={"Accept": "application/json"},
            data={
                "client_id": settings.GITHUB_CLIENT_ID,
                "client_secret": settings.GITHUB_CLIENT_SECRET,
                "code": request.code,
                "redirect_uri": settings.GITHUB_REDIRECT_URI,
            },
        )
        
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to get access token from GitHub")
            
        data = response.json()
        if "error" in data:
            raise HTTPException(status_code=400, detail=data.get("error_description", "OAuth error"))
            
        access_token = data["access_token"]
        scopes = data.get("scope", "repo,user")

        # Get GitHub user profile
        user_response = await client.get(
            "https://api.github.com/user",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/vnd.github+json"
            }
        )
        profile = user_response.json()
        account_id = str(profile.get("id"))
        account_name = profile.get("login")

    # Upsert the connection
    result = await db.execute(
        select(PlatformConnection).where(
            PlatformConnection.user_id == current_user.id,
            PlatformConnection.platform == "github"
        )
    )
    connection = result.scalar_one_or_none()
    
    if connection:
        connection.access_token_encrypted = access_token
        connection.scopes = scopes
        connection.account_id = account_id
        connection.account_name = account_name
    else:
        connection = PlatformConnection(
            user_id=current_user.id,
            platform="github",
            access_token_encrypted=access_token, # We are not encrypting for MVP
            scopes=scopes,
            account_id=account_id,
            account_name=account_name,
        )
        db.add(connection)
        
    await db.commit()
    
    return {"status": "success", "platform": "github", "account": account_name}


@router.delete("/{platform}", status_code=status.HTTP_204_NO_CONTENT)
async def disconnect_platform(
    platform: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Disconnect a platform."""
    result = await db.execute(
        select(PlatformConnection).where(
            PlatformConnection.user_id == current_user.id,
            PlatformConnection.platform == platform
        )
    )
    connection = result.scalar_one_or_none()
    
    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{platform} is not connected.",
        )
        
    await db.delete(connection)
    await db.commit()
