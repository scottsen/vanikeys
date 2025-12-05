"""
VaniKeys API client for CLI.

Handles communication with the VaniKeys server for ordering, status checks, etc.
"""

import os
from typing import Any, Optional
from dataclasses import dataclass

import httpx


@dataclass
class OrderResponse:
    """Response from order creation."""

    order_id: str
    pattern: str
    difficulty: str
    estimated_time: str
    cost_usd: float
    status: str


@dataclass
class OrderStatus:
    """Order status response."""

    order_id: str
    status: str  # PENDING, SEARCHING, FOUND, FAILED
    pattern: str
    progress: Optional[dict] = None  # {paths_tested: int, estimated_total: int}
    result: Optional[dict] = None  # {path: int, fingerprint: str, public_key: str}
    proof: Optional[dict] = None  # Cryptographic proof


class VaniKeysAPIClient:
    """Client for VaniKeys API."""

    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None):
        """Initialize API client.

        Args:
            base_url: API base URL (default: from env VANIKEYS_API_URL or production)
            api_key: API key (default: from env VANIKEYS_API_KEY)
        """
        self.base_url = (
            base_url
            or os.getenv("VANIKEYS_API_URL")
            or "https://api.vanikeys.dev/v1"
        )
        self.api_key = api_key or os.getenv("VANIKEYS_API_KEY")

        self.client = httpx.Client(
            base_url=self.base_url,
            timeout=30.0,
            headers=self._get_headers(),
        )

    def _get_headers(self) -> dict[str, str]:
        """Get request headers."""
        headers = {
            "User-Agent": "vanikeys-cli/0.2.0",
            "Content-Type": "application/json",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def create_order(
        self, pattern: str, root_public_key: str, key_type: str = "ssh"
    ) -> OrderResponse:
        """Create a vanity key order.

        Args:
            pattern: Pattern to search for (e.g., "dev123")
            root_public_key: Customer's root public key (hex)
            key_type: Type of key (default: "ssh")

        Returns:
            OrderResponse with order details

        Raises:
            httpx.HTTPError: If request fails
        """
        response = self.client.post(
            "/orders",
            json={
                "pattern": pattern,
                "root_public_key": root_public_key,
                "key_type": key_type,
            },
        )
        response.raise_for_status()
        data = response.json()

        return OrderResponse(
            order_id=data["order_id"],
            pattern=data["pattern"],
            difficulty=data["difficulty"],
            estimated_time=data["estimated_time"],
            cost_usd=data["cost_usd"],
            status=data["status"],
        )

    def get_order_status(self, order_id: str) -> OrderStatus:
        """Get order status.

        Args:
            order_id: Order ID (e.g., "ord_abc123xyz")

        Returns:
            OrderStatus with current status

        Raises:
            httpx.HTTPError: If request fails
        """
        response = self.client.get(f"/orders/{order_id}")
        response.raise_for_status()
        data = response.json()

        return OrderStatus(
            order_id=data["order_id"],
            status=data["status"],
            pattern=data["pattern"],
            progress=data.get("progress"),
            result=data.get("result"),
            proof=data.get("proof"),
        )

    def get_order_proof(self, order_id: str) -> dict:
        """Get cryptographic proof for an order.

        Args:
            order_id: Order ID

        Returns:
            Proof dictionary

        Raises:
            httpx.HTTPError: If request fails
        """
        response = self.client.get(f"/orders/{order_id}/proof")
        response.raise_for_status()
        return response.json()

    def close(self) -> None:
        """Close HTTP client."""
        self.client.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
