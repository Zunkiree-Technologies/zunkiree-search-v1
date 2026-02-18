"""Background health-check loop for OAuth connectors."""

from __future__ import annotations

import asyncio
import json
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_maker
from app.models import Connector
from app.services.oauth_registry import get_provider
from app.services.oauth_service import get_oauth_service

HEALTH_CHECK_INTERVAL = 300  # 5 minutes


async def health_check_loop() -> None:
    """Run forever, checking OAuth connector health every 5 minutes."""
    service = get_oauth_service()

    while True:
        await asyncio.sleep(HEALTH_CHECK_INTERVAL)
        try:
            async with async_session_maker() as db:
                result = await db.execute(
                    select(Connector).where(
                        Connector.auth_method == "oauth",
                        Connector.is_active == True,
                        Connector.connection_status != "disconnected",
                    )
                )
                connectors = result.scalars().all()

                for connector in connectors:
                    provider = get_provider(connector.app_name)
                    if not provider or not provider.userinfo_url:
                        continue

                    creds = json.loads(connector.credentials) if connector.credentials else {}
                    access_token = creds.get("access_token", "")
                    if not access_token:
                        continue

                    healthy, message = await service.check_connection_health(provider, access_token)

                    if healthy:
                        connector.connection_status = "connected"
                        connector.status_message = None
                    else:
                        # Attempt token refresh
                        refresh_token = creds.get("refresh_token")
                        if refresh_token:
                            try:
                                new_tokens = await service.refresh_access_token(provider, refresh_token)
                                creds["access_token"] = new_tokens.get("access_token", access_token)
                                if "refresh_token" in new_tokens:
                                    creds["refresh_token"] = new_tokens["refresh_token"]
                                connector.credentials = json.dumps(creds)
                                connector.connection_status = "connected"
                                connector.status_message = None
                            except Exception:
                                connector.connection_status = "error"
                                connector.status_message = message
                        else:
                            connector.connection_status = "error"
                            connector.status_message = message

                    connector.last_health_check_at = datetime.utcnow()

                await db.commit()

        except Exception as e:
            print(f"[health_check] Error: {e}")
