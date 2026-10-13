"""
Authentication and identity dependencies.

Provides header-based identity extraction for users (X-User-Id) and worker peers (X-Peer-Id).
Designed to be seamlessly swappable with JWT / OAuth bearer tokens in later phases.
"""

import uuid
from typing import Annotated

from fastapi import Header, HTTPException, status

from coordinator.config import settings


async def get_current_user_id(
    x_user_id: Annotated[str | None, Header(description="UUID of the authenticated user")] = None,
) -> uuid.UUID:
    """Extract and validate the client User UUID from headers.

    If X-User-Id is omitted and settings.demo_auth_enabled is True, falls back to the deterministic
    demo user ID (settings.demo_user_id). In production (demo_auth_enabled=False), X-User-Id is strictly required.
    """
    if not x_user_id:
        if settings.demo_auth_enabled:
            return uuid.UUID(settings.demo_user_id)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing required header: X-User-Id",
        )
    try:
        return uuid.UUID(x_user_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Malformed X-User-Id header: '{x_user_id}' is not a valid UUID",
        ) from exc


async def get_current_peer_id(
    x_peer_id: Annotated[str | None, Header(description="UUID of the worker peer node")] = None,
    x_worker_id: Annotated[str | None, Header(description="Alias header for worker peer node UUID")] = None,
) -> uuid.UUID:
    """Extract and validate the worker Peer UUID from headers.

    Supports either canonical X-Peer-Id or worker X-Worker-ID header.
    """
    peer_raw = x_peer_id or x_worker_id
    if not peer_raw:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing required header: X-Peer-Id or X-Worker-ID",
        )
    try:
        return uuid.UUID(peer_raw)
    except ValueError as exc:
        if x_worker_id and not x_peer_id:
            # Deterministically convert string worker identifier to UUID
            return uuid.uuid5(uuid.NAMESPACE_DNS, peer_raw)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Malformed peer ID header: '{peer_raw}' is not a valid UUID",
        ) from exc
