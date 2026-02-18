from __future__ import annotations

import json
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import get_settings
from app.database import get_db
from app.models import Customer, Connector
from app.api.client import get_current_customer
from app.services.notion_sync import get_notion_sync_service
from app.services.oauth_registry import (
    get_provider,
    get_all_providers,
    is_provider_configured,
    has_oauth_support,
)
from app.services.oauth_service import (
    get_oauth_service,
    state_store,
    extract_account_name,
)

router = APIRouter(prefix="/client/connectors", tags=["connectors"])

SYNCABLE_APPS = ["notion"]


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class ConnectionInfo(BaseModel):
    id: str
    display_name: str
    external_account_name: str | None
    connection_status: str
    status_message: str | None
    is_syncable: bool
    last_synced_at: str | None


class AppResponse(BaseModel):
    provider_id: str
    display_name: str
    icon: str
    category: str
    description: str
    is_configured: bool
    is_connectable: bool
    connections: list[ConnectionInfo]


class AppsListResponse(BaseModel):
    apps: list[AppResponse]
    categories: list[str]


class ConnectorResponse(BaseModel):
    id: str
    app_name: str
    display_name: str
    auth_method: str
    connection_status: str
    status_message: str | None
    external_account_name: str | None
    is_active: bool
    is_syncable: bool
    last_synced_at: str | None
    last_health_check_at: str | None
    created_at: str
    updated_at: str


class ConnectorListResponse(BaseModel):
    connectors: list[ConnectorResponse]
    total: int


class CreateConnectorRequest(BaseModel):
    app_name: str = Field(..., min_length=1, max_length=100)
    display_name: str | None = Field(None, max_length=255)
    credentials: dict = Field(default_factory=dict)


class SyncResponse(BaseModel):
    job_id: str
    status: str
    chunks_created: int
    message: str


class AuthorizeResponse(BaseModel):
    authorization_url: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def connector_to_response(c: Connector) -> ConnectorResponse:
    return ConnectorResponse(
        id=str(c.id),
        app_name=c.app_name,
        display_name=c.display_name,
        auth_method=c.auth_method,
        connection_status=c.connection_status,
        status_message=c.status_message,
        external_account_name=c.external_account_name,
        is_active=c.is_active,
        is_syncable=c.app_name in SYNCABLE_APPS,
        last_synced_at=c.last_synced_at.isoformat() if c.last_synced_at else None,
        last_health_check_at=c.last_health_check_at.isoformat() if c.last_health_check_at else None,
        created_at=c.created_at.isoformat(),
        updated_at=c.updated_at.isoformat(),
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/apps", response_model=AppsListResponse)
async def list_apps(
    customer: Customer = Depends(get_current_customer),
    db: AsyncSession = Depends(get_db),
):
    """Return all providers merged with this customer's connection state."""
    # Fetch customer's existing connectors
    result = await db.execute(
        select(Connector)
        .where(Connector.customer_id == customer.id)
        .order_by(Connector.created_at.desc())
    )
    connectors = result.scalars().all()

    # Index connectors by app_name
    connectors_by_app: dict[str, list[Connector]] = {}
    for c in connectors:
        connectors_by_app.setdefault(c.app_name, []).append(c)

    providers = get_all_providers()
    categories_seen: set[str] = set()
    categories: list[str] = []
    apps: list[AppResponse] = []

    for p in providers:
        if p.category not in categories_seen:
            categories_seen.add(p.category)
            categories.append(p.category)

        app_connectors = connectors_by_app.get(p.provider_id, [])
        connections = [
            ConnectionInfo(
                id=str(c.id),
                display_name=c.display_name,
                external_account_name=c.external_account_name,
                connection_status=c.connection_status,
                status_message=c.status_message,
                is_syncable=c.app_name in SYNCABLE_APPS,
                last_synced_at=c.last_synced_at.isoformat() if c.last_synced_at else None,
            )
            for c in app_connectors
        ]

        apps.append(AppResponse(
            provider_id=p.provider_id,
            display_name=p.display_name,
            icon=p.icon,
            category=p.category,
            description=p.description,
            is_configured=is_provider_configured(p),
            is_connectable=has_oauth_support(p) or p.provider_id == "custom",
            connections=connections,
        ))

    return AppsListResponse(apps=apps, categories=categories)


@router.get("/oauth/{provider_id}/authorize", response_model=AuthorizeResponse)
async def oauth_authorize(
    provider_id: str,
    request: Request,
    customer: Customer = Depends(get_current_customer),
):
    """Start an OAuth flow — returns the authorization URL."""
    provider = get_provider(provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail=f"Unknown provider: {provider_id}")
    if not has_oauth_support(provider):
        raise HTTPException(status_code=400, detail=f"Provider {provider_id} does not support OAuth")

    # Build callback URL relative to where the API is running
    callback_url = str(request.base_url).rstrip("/") + f"/api/v1/client/connectors/oauth/callback"

    service = get_oauth_service()
    auth_url = await service.get_authorization_url(
        provider=provider,
        customer_id=str(customer.id),
        callback_url=callback_url,
    )
    return AuthorizeResponse(authorization_url=auth_url)


@router.get("/oauth/callback")
async def oauth_callback(
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """OAuth callback — unauthenticated, browser redirect from provider."""
    settings = get_settings()
    admin_url = settings.client_admin_url.rstrip("/")

    if error:
        return RedirectResponse(f"{admin_url}/index.html?oauth_error={error}")

    if not state or not code:
        return RedirectResponse(f"{admin_url}/index.html?oauth_error=missing_params")

    # Consume state token
    entry = state_store.consume(state)
    if not entry:
        return RedirectResponse(f"{admin_url}/index.html?oauth_error=invalid_state")

    provider = get_provider(entry.provider_id)
    if not provider:
        return RedirectResponse(f"{admin_url}/index.html?oauth_error=unknown_provider")

    service = get_oauth_service()

    # Build the same callback URL used during authorize
    # We need to derive it from the current request context
    callback_url = str(f"{admin_url}").replace(admin_url, "")  # placeholder
    # The callback URL needs to match what was sent in authorize.
    # Since we're in the callback itself, we reconstruct it.
    import os
    # Use a simple heuristic: the callback URL is at the API's base
    api_base = os.getenv("API_BASE_URL", "http://localhost:8000")
    callback_url = f"{api_base}/api/v1/client/connectors/oauth/callback"

    try:
        # Exchange code for tokens
        token_data = await service.exchange_code(
            provider=provider,
            code=code,
            callback_url=callback_url,
        )

        access_token = token_data.get("access_token", "")
        refresh_token = token_data.get("refresh_token", "")

        # Fetch user info
        account_name = ""
        external_id = ""
        if provider.userinfo_url and access_token:
            try:
                userinfo = await service.fetch_user_info(provider, access_token)
                account_name = extract_account_name(provider, userinfo)
                external_id = userinfo.get("id", userinfo.get("sub", ""))
                if external_id and not isinstance(external_id, str):
                    external_id = str(external_id)
            except Exception as e:
                print(f"[oauth_callback] Failed to fetch userinfo: {e}")

        # Store tokens as JSON credentials
        credentials = {"access_token": access_token}
        if refresh_token:
            credentials["refresh_token"] = refresh_token
        # Include any other token fields (e.g. token_type, expires_in)
        for key in ("token_type", "scope", "workspace_id", "workspace_name"):
            if key in token_data:
                credentials[key] = token_data[key]

        # Determine token expiry
        token_expires_at = None
        if "expires_in" in token_data:
            from datetime import timedelta
            token_expires_at = datetime.utcnow() + timedelta(seconds=int(token_data["expires_in"]))

        connector = Connector(
            customer_id=uuid.UUID(entry.customer_id),
            app_name=provider.provider_id,
            display_name=account_name or provider.display_name,
            credentials=json.dumps(credentials),
            is_active=True,
            auth_method="oauth",
            connection_status="connected",
            external_account_id=external_id or None,
            external_account_name=account_name or None,
            token_expires_at=token_expires_at,
        )
        db.add(connector)
        await db.commit()

        return RedirectResponse(f"{admin_url}/index.html?oauth_success={provider.provider_id}")

    except Exception as e:
        print(f"[oauth_callback] Error: {e}")
        return RedirectResponse(f"{admin_url}/index.html?oauth_error={provider.provider_id}")


@router.post("/{connector_id}/disconnect")
async def disconnect_connector(
    connector_id: uuid.UUID,
    customer: Customer = Depends(get_current_customer),
    db: AsyncSession = Depends(get_db),
):
    """Disconnect an OAuth connector — clears tokens, sets status to disconnected."""
    result = await db.execute(
        select(Connector).where(
            Connector.id == connector_id,
            Connector.customer_id == customer.id,
        )
    )
    connector = result.scalar_one_or_none()
    if not connector:
        raise HTTPException(status_code=404, detail="Connector not found")

    connector.credentials = json.dumps({})
    connector.connection_status = "disconnected"
    connector.status_message = "Disconnected by user"
    connector.is_active = False
    connector.updated_at = datetime.utcnow()
    await db.commit()

    return {"message": "Connector disconnected"}


# ---------------------------------------------------------------------------
# Existing endpoints (kept with updated response models)
# ---------------------------------------------------------------------------

@router.get("/", response_model=ConnectorListResponse)
async def list_connectors(
    customer: Customer = Depends(get_current_customer),
    db: AsyncSession = Depends(get_db),
):
    """List all connectors for the current customer."""
    result = await db.execute(
        select(Connector)
        .where(Connector.customer_id == customer.id)
        .order_by(Connector.created_at.desc())
    )
    connectors = result.scalars().all()
    return ConnectorListResponse(
        connectors=[connector_to_response(c) for c in connectors],
        total=len(connectors),
    )


@router.post("/", response_model=ConnectorResponse, status_code=201)
async def create_connector(
    request: CreateConnectorRequest,
    customer: Customer = Depends(get_current_customer),
    db: AsyncSession = Depends(get_db),
):
    """Create a custom connector (for non-OAuth / custom app type)."""
    app_name = request.app_name.lower()

    display_name = request.display_name
    if not display_name:
        display_name = request.credentials.get("username") or app_name.title()

    connector = Connector(
        customer_id=customer.id,
        app_name=app_name,
        display_name=display_name,
        credentials=json.dumps(request.credentials),
        is_active=True,
        auth_method="credential",
        connection_status="connected",
    )
    db.add(connector)
    await db.commit()
    await db.refresh(connector)

    return connector_to_response(connector)


@router.get("/{connector_id}", response_model=ConnectorResponse)
async def get_connector(
    connector_id: uuid.UUID,
    customer: Customer = Depends(get_current_customer),
    db: AsyncSession = Depends(get_db),
):
    """Get a single connector."""
    result = await db.execute(
        select(Connector).where(
            Connector.id == connector_id,
            Connector.customer_id == customer.id,
        )
    )
    connector = result.scalar_one_or_none()
    if not connector:
        raise HTTPException(status_code=404, detail="Connector not found")

    return connector_to_response(connector)


@router.delete("/{connector_id}")
async def delete_connector(
    connector_id: uuid.UUID,
    customer: Customer = Depends(get_current_customer),
    db: AsyncSession = Depends(get_db),
):
    """Delete a connector."""
    result = await db.execute(
        select(Connector).where(
            Connector.id == connector_id,
            Connector.customer_id == customer.id,
        )
    )
    connector = result.scalar_one_or_none()
    if not connector:
        raise HTTPException(status_code=404, detail="Connector not found")

    await db.delete(connector)
    await db.commit()

    return {"message": "Connector deleted"}


@router.post("/{connector_id}/sync", response_model=SyncResponse)
async def sync_connector(
    connector_id: uuid.UUID,
    customer: Customer = Depends(get_current_customer),
    db: AsyncSession = Depends(get_db),
):
    """Trigger a sync for a connector (Notion only for now)."""
    result = await db.execute(
        select(Connector).where(
            Connector.id == connector_id,
            Connector.customer_id == customer.id,
        )
    )
    connector = result.scalar_one_or_none()
    if not connector:
        raise HTTPException(status_code=404, detail="Connector not found")

    if connector.app_name not in SYNCABLE_APPS:
        raise HTTPException(status_code=400, detail=f"Sync not supported for {connector.app_name}")

    if not connector.is_active:
        raise HTTPException(status_code=400, detail="Connector is inactive")

    try:
        if connector.app_name == "notion":
            service = get_notion_sync_service()
            job = await service.sync_connector(
                db=db,
                connector=connector,
                site_id=customer.site_id,
            )
            return SyncResponse(
                job_id=str(job.id),
                status=job.status,
                chunks_created=job.chunks_created,
                message=f"Notion sync completed. {job.chunks_created} chunks created.",
            )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"code": "SYNC_FAILED", "message": str(e)},
        )
