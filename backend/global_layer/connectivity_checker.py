"""
connectivity_checker.py — Global Intelligence Layer
-----------------------------------------------------
Determines whether the service is operating in ONLINE or OFFLINE mode.

Design constraints:
  - Never raises an exception; always returns a clean ConnectivityStatus.
  - Never blocks for more than TIMEOUT_SECONDS.
  - Failures are silently absorbed and treated as OFFLINE.
  - Does not perform DNS or TCP checks for external services; uses a
    lightweight HTTPS HEAD request to a reliable, low-latency endpoint.
"""

import asyncio
import logging
from enum import Enum
from dataclasses import dataclass

import httpx

logger = logging.getLogger(__name__)

# Target used for connectivity probe — small, reliable, low-latency.
_PROBE_URL = "https://www.google.com"
_TIMEOUT_SECONDS = 3.0


class ConnectivityMode(str, Enum):
    """Represents the determined connectivity state of the service."""
    ONLINE = "ONLINE"
    OFFLINE = "OFFLINE"


@dataclass(frozen=True)
class ConnectivityStatus:
    """Result of a connectivity check."""
    mode: ConnectivityMode
    reason: str  # Human-readable reason, for internal logging only.

    @property
    def is_online(self) -> bool:
        return self.mode == ConnectivityMode.ONLINE

    @property
    def is_offline(self) -> bool:
        return self.mode == ConnectivityMode.OFFLINE


async def check_connectivity() -> ConnectivityStatus:
    """
    Perform an async connectivity probe.

    Returns
    -------
    ConnectivityStatus
        Always returns; never raises. On any failure, returns OFFLINE.
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.head(
                _PROBE_URL,
                timeout=_TIMEOUT_SECONDS,
                follow_redirects=True,
            )
            if response.status_code < 500:
                return ConnectivityStatus(
                    mode=ConnectivityMode.ONLINE,
                    reason=f"Probe succeeded (HTTP {response.status_code})",
                )
            # 5xx from the probe target itself → treat as OFFLINE
            return ConnectivityStatus(
                mode=ConnectivityMode.OFFLINE,
                reason=f"Probe returned HTTP {response.status_code}",
            )

    except httpx.TimeoutException:
        logger.debug("connectivity_checker.timeout probe_url=%s", _PROBE_URL)
        return ConnectivityStatus(
            mode=ConnectivityMode.OFFLINE,
            reason="Connectivity probe timed out",
        )

    except httpx.ConnectError:
        logger.debug("connectivity_checker.connect_error probe_url=%s", _PROBE_URL)
        return ConnectivityStatus(
            mode=ConnectivityMode.OFFLINE,
            reason="Connection refused or network unreachable",
        )

    except Exception:
        # Catch-all: any unexpected error must not crash the pipeline.
        logger.exception("connectivity_checker.unexpected_error — defaulting to OFFLINE")
        return ConnectivityStatus(
            mode=ConnectivityMode.OFFLINE,
            reason="Unexpected error during connectivity probe",
        )


def check_connectivity_sync() -> ConnectivityStatus:
    """
    Synchronous wrapper for environments that cannot use async/await.
    Prefers an existing event loop; falls back to creating a new one.
    """
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Running inside an existing event loop (e.g. tests, Jupyter).
            # Schedule as a task and return a safe default immediately.
            logger.debug("connectivity_checker.sync_called_in_async_context — defaulting ONLINE")
            return ConnectivityStatus(
                mode=ConnectivityMode.ONLINE,
                reason="Sync check skipped (async loop already running)",
            )
        return loop.run_until_complete(check_connectivity())
    except Exception:
        logger.exception("connectivity_checker.sync_wrapper_error — defaulting ONLINE")
        return ConnectivityStatus(
            mode=ConnectivityMode.ONLINE,
            reason="Sync wrapper error — safe default ONLINE",
        )
