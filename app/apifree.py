import os
import time
import requests

API_KEY = os.getenv("APIFREE_API_KEY")
BASE_URL = "https://api.skycoding.ai"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

# ---------- IMAGE ----------
def generate_image(image_url, prompt, model="google/nano-banana-pro/edit"):
    payload = {
        "model": model,
        "image": image_url,
        "prompt": prompt,
        "aspect_ratio": "1:1",
        "resolution": "1K"
    }

    r = requests.post(f"{BASE_URL}/v1/image/submit", headers=headers, json=payload)
    data = r.json()

    if data.get("code") != 200:
        raise Exception(data)

    request_id = data["resp_data"]["request_id"]

    while True:
        time.sleep(2)
        r = requests.get(f"{BASE_URL}/v1/image/{request_id}/result", headers=headers)
        d = r.json()

        if d["resp_data"]["status"] == "success":
            return d["resp_data"]["image_list"][0]


# ---------- VIDEO ----------
def generate_video(image_url, prompt, model="klingai/kling-v2.6/pro/image-to-video"):
    payload = {
        "model": model,
        "image": image_url,
        "prompt": prompt,
        "duration": 5
    }

    r = requests.post(f"{BASE_URL}/v1/video/submit", headers=headers, json=payload)
    data = r.json()

    if data.get("code") != 200:
        raise Exception(data)

    request_id = data["resp_data"]["request_id"]

    while True:
        time.sleep(5)
        r = requests.get(f"{BASE_URL}/v1/video/{request_id}/status", headers=headers)
        d = r.json()

        if d["resp_data"]["status"] == "success":
            break

    r = requests.get(f"{BASE_URL}/v1/video/{request_id}/result", headers=headers)
    d = r.json()

    return d["resp_data"]["video_list"][0]


# ---------- CHAT ----------
def chat_gpt(message, model="openai/gpt-5.2"):
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": message}],
        "max_tokens": 4096
    }

    r = requests.post(f"{BASE_URL}/v1/chat/completions", headers=headers, json=payload)
    data = r.json()

    return data["choices"][0]["message"]["content"]
