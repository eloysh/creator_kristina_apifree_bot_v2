from __future__ import annotations

import os
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from .config import settings
from .storage import Storage
from .telegram_api import TelegramAPI
from .apifree_client import ApiFreeClient
from .bot_logic import handle_update

app = FastAPI(title="Creator Kristina Bot (ApiFree)")

storage = Storage(settings.DB_PATH)
tg = TelegramAPI(settings.BOT_TOKEN)
apifree = ApiFreeClient(settings.APIFREE_BASE_URL, settings.APIFREE_API_KEY)

@app.on_event("startup")
async def startup():
    os.makedirs(os.path.dirname(settings.DB_PATH) or ".", exist_ok=True)
    await storage.init()

    # set webhook
    webhook_url = f"{settings.PUBLIC_BASE_URL.rstrip('/')}/telegram/webhook/{settings.WEBHOOK_SECRET}"
    try:
        await tg.set_webhook(webhook_url)
        print(f"[startup] setWebhook -> {webhook_url}")
    except Exception as e:
        print(f"[startup] setWebhook failed: {e}")

@app.get("/health")
async def health():
    return {"ok": True}

@app.post("/telegram/webhook/{secret}")
async def telegram_webhook(secret: str, request: Request):
    if secret != settings.WEBHOOK_SECRET:
        raise HTTPException(status_code=404, detail="Not found")
    update = await request.json()
    # optional: inject bot username if you set BOT_USERNAME env, otherwise ignore
    update["bot_username"] = os.getenv("BOT_USERNAME", "")
    try:
        await handle_update(storage, tg, apifree, update)
    except Exception as e:
        print("handle_update error:", e)
    return {"ok": True}

# -------- Mini App API --------
@app.get("/api/me")
async def api_me(tg_id: int):
    u = await storage.get_user(tg_id)
    if not u:
        raise HTTPException(status_code=404, detail="user not found")
    return {"tg_id": u.tg_id, "credits_free": u.credits_free, "credits_pro": u.credits_pro}

@app.post("/api/chat")
async def api_chat(payload: dict):
    tg_id = int(payload.get("tg_id", 0))
    text = (payload.get("text") or "").strip()
    if not tg_id or not text:
        raise HTTPException(status_code=400, detail="tg_id and text required")
    # Admins bypass credit checks (useful while payments/referrals are being wired)
    if tg_id not in settings.admin_ids():
        ok = await storage.consume_credit(tg_id)
        if not ok:
            return JSONResponse({"ok": False, "error": "no_credits"}, status_code=402)

    try:
        answer = await apifree.chat(settings.APIFREE_CHAT_MODEL, [{"role": "user", "content": text}])
        return {"ok": True, "answer": answer}
    except Exception as e:
        # Make provider errors readable in the UI
        return JSONResponse({"ok": False, "error": "provider_error", "detail": str(e)}, status_code=502)

@app.post("/api/image/submit")
async def api_image_submit(payload: dict):
    tg_id = int(payload.get("tg_id", 0))
    prompt = (payload.get("prompt") or "").strip()
    if not tg_id or not prompt:
        raise HTTPException(status_code=400, detail="tg_id and prompt required")
    if tg_id not in settings.admin_ids():
        ok = await storage.consume_credit(tg_id)
        if not ok:
            return JSONResponse({"ok": False, "error": "no_credits"}, status_code=402)

    try:
        res = await apifree.image_submit(
            model=settings.APIFREE_IMAGE_MODEL,
            prompt=prompt,
            negative_prompt=payload.get("negative_prompt"),
            width=payload.get("width"),
            height=payload.get("height"),
            num_images=int(payload.get("num_images", 1)),
        )
        return {"ok": True, "apifree": res}
    except Exception as e:
        return JSONResponse({"ok": False, "error": "provider_error", "detail": str(e)}, status_code=502)

@app.get("/api/image/result/{request_id}")
async def api_image_result(request_id: str):
    res = await apifree.image_result(request_id)
    return {"ok": True, "apifree": res}

@app.post("/api/video/submit")
async def api_video_submit(payload: dict):
    tg_id = int(payload.get("tg_id", 0))
    prompt = (payload.get("prompt") or "").strip()
    if not tg_id or not prompt:
        raise HTTPException(status_code=400, detail="tg_id and prompt required")
    if tg_id not in settings.admin_ids():
        ok = await storage.consume_credit(tg_id)
        if not ok:
            return JSONResponse({"ok": False, "error": "no_credits"}, status_code=402)

    try:
        res = await apifree.video_submit(
            model=settings.APIFREE_VIDEO_MODEL,
            prompt=prompt,
            negative_prompt=payload.get("negative_prompt"),
            width=payload.get("width"),
            height=payload.get("height"),
            duration=payload.get("duration"),
            fps=payload.get("fps"),
        )
        return {"ok": True, "apifree": res}
    except Exception as e:
        return JSONResponse({"ok": False, "error": "provider_error", "detail": str(e)}, status_code=502)

@app.get("/api/video/result/{request_id}")
async def api_video_result(request_id: str):
    res = await apifree.video_result(request_id)
    return {"ok": True, "apifree": res}

# -------- static miniapp --------
WEBAPP_DIR = os.path.join(os.path.dirname(__file__), "..", "webapp")
app.mount("/webapp", StaticFiles(directory=WEBAPP_DIR, html=True), name="webapp")

@app.get("/")
async def root():
    return HTMLResponse("""<html><body>
    <h3>Creator Kristina Bot</h3>
    <ul>
      <li><a href='/webapp/'>Open Mini App</a></li>
      <li><a href='/health'>Health</a></li>
    </ul>
    </body></html>""")
