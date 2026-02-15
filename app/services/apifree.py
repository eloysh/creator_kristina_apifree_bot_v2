import httpx
import asyncio
from app.config import settings

API_URL = "https://api.apifree.ai/v1/inference"


async def _submit(model: str, payload: dict):
    headers = {
        "Authorization": f"Bearer {settings.APIFREE_API_KEY}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=120) as client:
        r = await client.post(
            "https://api.apifree.ai/v1/inference",
            headers=headers,
            json={"model": model, "input": payload},
        )

        data = r.json()
        print("API SUBMIT RESPONSE:", data)   

        # ApiFree может вернуть id вместо task_id
        task_id = data.get("task_id") or data.get("id")

        return {"task_id": task_id}



async def _wait_result(task_id: str):
    headers = {"Authorization": f"Bearer {settings.APIFREE_API_KEY}"}
    url = f"https://api.apifree.ai/v1/task/{task_id}"

    async with httpx.AsyncClient(timeout=120) as client:
        for _ in range(40):  # ждать до ~40 сек
            r = await client.get(url, headers=headers)
            data = r.json()

            if data.get("status") == "succeeded":
                return data["output"]

            if data.get("status") == "succeeded":
    output = data.get("output") or {}
    return output


            await asyncio.sleep(1)

    return None


# ---------- IMAGE ----------

async def generate_image(prompt: str):
    submit = await _submit(
        settings.APIFREE_IMAGE_MODEL,
        {"prompt": prompt}
    )

    task_id = submit.get("task_id")
    if not task_id:
        return None

    result = await _wait_result(task_id)
    if not result:
        return None

    return result.get("url")


# ---------- VIDEO ----------

async def generate_video(prompt: str):
    submit = await _submit(
        settings.APIFREE_VIDEO_MODEL,
        {"prompt": prompt}
    )

    task_id = submit.get("task_id")
    if not task_id:
        return None

    result = await _wait_result(task_id)
    if not result:
        return None

    return result.get("url")


# ---------- CHAT ----------

async def chat_gpt(message: str):
    submit = await _submit(
        settings.APIFREE_CHAT_MODEL,
        {"messages": [{"role": "user", "content": message}]}
    )

    return submit.get("output", "")
