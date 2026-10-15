"""Thin Blynk HTTPS API client for the heat-stress dashboard."""
import os
import random
import requests
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("BLYNK_TOKEN", "")
SERVER = os.getenv("BLYNK_SERVER", "blynk.cloud")

# EDIT THIS to match your ESP32 firmware's virtual pins.
PINS = {
    "temperature": "V0",
    "bpm": "V1",
    "baseline": "V2",
    "deviation": "V3",
    "trend": "V4",
    "risk": "V5",
    "action": "V6",
    "status": "V7",
}

NUMERIC = {"temperature", "bpm", "baseline", "deviation"}


def _to_number(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def is_device_online() -> bool:
    try:
        r = requests.get(
            f"https://{SERVER}/external/api/isHardwareConnected",
            params={"token": TOKEN},
            timeout=5,
        )
        return r.text.strip().lower() == "true"
    except requests.RequestException:
        return False


def read_all() -> dict:
    """Read all pins in one request. Returns {name: value}."""
    pins = "&".join(p.lower() for p in PINS.values())
    url = f"https://{SERVER}/external/api/get?token={TOKEN}&{pins}"
    r = requests.get(url, timeout=8)
    r.raise_for_status()
    raw = r.json()  # {"v0": "31.2", "v1": "78", ...}
    out = {}
    for name, pin in PINS.items():
        val = raw.get(pin.lower())
        out[name] = _to_number(val) if name in NUMERIC else val
    return out


def write_pin(pin: str, value) -> None:
    """Write a value to a virtual pin (used in Phase 2 for AI advice)."""
    requests.get(
        f"https://{SERVER}/external/api/update",
        params={"token": TOKEN, pin.lower(): value},
        timeout=8,
    ).raise_for_status()


def demo_reading(step: int) -> dict:
    """Simulated data so the UI can be tested without hardware."""
    baseline = 74
    bpm = baseline + min(step, 30) + random.randint(-2, 2)
    dev = bpm - baseline
    temp = round(31 + min(step, 30) * 0.2 + random.random(), 1)
    if dev >= 22:
        risk, action, trend = "HIGH WARNING", "STOP + COOL", "RISING"
    elif dev >= 12:
        risk, action, trend = "CAUTION", "REST + HYDRATE", "RISING"
    else:
        risk, action, trend = "NORMAL", "CONTINUE WORK", "STABLE"
    return {
        "temperature": temp, "bpm": bpm, "baseline": baseline,
        "deviation": dev, "trend": trend, "risk": risk,
        "action": action, "status": "DEMO",
    }
