from typing import Any

import httpx


class ServiceError(Exception):
    def __init__(self, service: str, status_code: int, detail: str):
        self.service = service
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


class ServiceClient:
    """Small HTTP client used by the gateway to keep service boundaries explicit."""

    async def request(self, service: str, method: str, url: str, **kwargs: Any) -> Any:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.request(method, url, **kwargs)
        except httpx.RequestError as exc:
            raise ServiceError(service, 503, f"{service} is unavailable: {exc}") from exc

        if response.status_code >= 400:
            try:
                detail = response.json().get("detail", response.text)
            except ValueError:
                detail = response.text
            raise ServiceError(service, response.status_code, str(detail))

        if response.status_code == 204:
            return None
        return response.json()

    async def get(self, service: str, url: str) -> Any:
        return await self.request(service, "GET", url)

    async def post(self, service: str, url: str, payload: dict[str, Any]) -> Any:
        return await self.request(service, "POST", url, json=payload)


client = ServiceClient()
