from __future__ import annotations

import httpx
from typing import Any, Dict, Optional, List

class ApiFreeClient:
    def __init__(self, base_url: str, api_key: str, timeout_s: float = 120.0):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout_s = timeout_s

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def chat(self, model: str, messages: List[Dict[str, str]], temperature: float = 0.7) -> str:
        # ApiFree supports OpenAI-like endpoint /v1/chat/completions (per docs)
        url = f"{self.base_url}/v1/chat/completions"
        payload = {"model": model, "messages": messages, "temperature": temperature}
        async with httpx.AsyncClient(timeout=self.timeout_s) as client:
            r = await client.post(url, headers=self._headers(), json=payload)
            r.raise_for_status()
            data = r.json()
            # OpenAI-style: choices[0].message.content
            return data["choices"][0]["message"]["content"]

    async def image_submit(self, model: str, prompt: str, negative_prompt: Optional[str]=None, width: Optional[int]=None, height: Optional[int]=None, num_images: int = 1) -> Dict[str, Any]:
        url = f"{self.base_url}/v1/image/submit"
        payload: Dict[str, Any] = {"model": model, "prompt": prompt, "num_images": num_images}
        if negative_prompt:
            payload["negative_prompt"] = negative_prompt
        if width:
            payload["width"] = width
        if height:
            payload["height"] = height
        async with httpx.AsyncClient(timeout=self.timeout_s) as client:
            r = await client.post(url, headers=self._headers(), json=payload)
            r.raise_for_status()
            return r.json()

    async def image_result(self, request_id: str) -> Dict[str, Any]:
        url = f"{self.base_url}/v1/image/{request_id}/result"
        async with httpx.AsyncClient(timeout=self.timeout_s) as client:
            r = await client.get(url, headers=self._headers())
            r.raise_for_status()
            return r.json()

    async def video_submit(self, model: str, prompt: str, negative_prompt: Optional[str]=None, width: Optional[int]=None, height: Optional[int]=None, duration: Optional[int]=None, fps: Optional[int]=None) -> Dict[str, Any]:
        url = f"{self.base_url}/v1/video/submit"
        payload: Dict[str, Any] = {"model": model, "prompt": prompt}
        if negative_prompt:
            payload["negative_prompt"] = negative_prompt
        if width:
            payload["width"] = width
        if height:
            payload["height"] = height
        if duration:
            payload["duration"] = duration
        if fps:
            payload["fps"] = fps
        async with httpx.AsyncClient(timeout=self.timeout_s) as client:
            r = await client.post(url, headers=self._headers(), json=payload)
            r.raise_for_status()
            return r.json()

    async def video_result(self, request_id: str) -> Dict[str, Any]:
        url = f"{self.base_url}/v1/video/{request_id}/result"
        async with httpx.AsyncClient(timeout=self.timeout_s) as client:
            r = await client.get(url, headers=self._headers())
            r.raise_for_status()
            return r.json()
