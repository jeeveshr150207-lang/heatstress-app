# Heat-Stress Dashboard (Phase 1)

## Run
```
python -m venv .venv
.venv\Scripts\activate        # Windows  (Mac/Linux: source .venv/bin/activate)
pip install -r requirements.txt
copy .env.example .env        # then edit .env with your Blynk token
streamlit run app.py
```
No token yet? Leave it blank. The app starts in Demo mode.

## Match your pins
Edit `PINS` in `blynk_client.py` to match your ESP32 firmware (default: V0 temp, V1 BPM,
V2 baseline, V3 deviation, V4 trend, V5 risk, V6 action, V7 status).

## Blynk server region
If reads fail, set BLYNK_SERVER in .env to your region (e.g. blr1.blynk.cloud).
