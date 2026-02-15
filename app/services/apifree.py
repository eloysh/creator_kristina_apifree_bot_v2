from __future__ import annotations

import asyncio
from typing import Any, Dict, Optional

import httpx


class ApiFreeService:
    """
    Примерная обёртка. Подстрой под реальные урлы/поля ApiFree.
    Главная идея: submit -> task_id, затем polling -> итоговый url.
    """

    def __init__(self, base_url: str, api_key: Optional[str] = None):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key

    def _headers(self) -> Dict[str, str]:
        h: Dict[str, str] = {"Content-Type": "application/json"}
        if self.api_key:
            h["Authorization"] = f"Bearer {self.api_key}"
        return h

    async def _post(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=60.0) as client:
            r = await client.post(f"{self.base_url}{path}", json=payload, headers=self._headers())
            r.raise_for_status()
            return r.json()

    async def _get(self, path: str) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=60.0) as client:
            r = await client.get(f"{self.base_url}{path}", headers=self._headers())
            r.raise_for_status()
            return r.json()

    async def submit_image(self, prompt: str) -> str:
        data = await self._post("/image/submit", {"prompt": prompt})
        # Подстрой под ApiFree: task_id / id / result.id
        task_id = data.get("task_id") or data.get("id") or (data.get("result") or {}).get("id")
        if not task_id:
            raise RuntimeError(f"ApiFree image submit: no task id in response: {data}")
        return str(task_id)

    async def get_image_result(self, task_id: str) -> Dict[str, Any]:
        # Подстрой под ApiFree
        return await self._get(f"/image/result/{task_id}")

    async def wait_image_url(self, task_id: str, timeout_sec: int = 180) -> str:
        t = 0
        while t < timeout_sec:
            res = await self.get_image_result(task_id)
            status = (res.get("status") or res.get("state") or "").lower()
            if status in ("done", "succeeded", "success", "completed"):
                url = res.get("url") or (res.get("result") or {}).get("url")
                if not url:
                    raise RuntimeError(f"ApiFree image done but no url: {res}")
                return url
            if status in ("failed", "error"):
                raise RuntimeError(f"ApiFree image failed: {res}")
            await asyncio.sleep(2)
            t += 2
        raise TimeoutError("ApiFree image timeout")

