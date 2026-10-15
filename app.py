"""Heat-Stress Early Warning: Blynk dashboard + AI advisor (Phase 2)."""
import time
from datetime import datetime

import altair as alt
import pandas as pd
import streamlit as st

import ai_advisor as ai
import blynk_client as bc

st.set_page_config(page_title="Heat-Stress Monitor", page_icon="🌡️", layout="wide")

COLORS = {"NORMAL": "#1b9e4b", "CAUTION": "#e6a100", "HIGH WARNING": "#d62828"}
# Chart line colours, in this order: bpm, baseline, temperature
LINE_COLORS = ["#e63946", "#8d99ae", "#ff9f1c"]


def chart(df, cols):
    d = df[cols].reset_index().melt("time", var_name="series", value_name="value")
    return alt.Chart(d).mark_line().encode(
        x=alt.X("time:N", axis=alt.Axis(labelOverlap=True, labelAngle=0)),
        y=alt.Y("value:Q", scale=alt.Scale(zero=False)),
        color=alt.Color("series:N", scale=alt.Scale(
            domain=["bpm", "baseline", "temperature"], range=LINE_COLORS)),
    ).properties(height=300)


# ---------- state ----------
ss = st.session_state
ss.setdefault("history", [])
ss.setdefault("alerts", [])
ss.setdefault("step", 0)
ss.setdefault("last_risk", None)
ss.setdefault("advice", None)
ss.setdefault("advice_time", 0.0)
ss.setdefault("advice_risk", None)

# ---------- sidebar ----------
st.sidebar.title("Settings")
demo = st.sidebar.toggle("Demo mode (simulated data)", value=not bc.TOKEN)
refresh = st.sidebar.slider("Refresh every (s)", 2, 30, 5)
keep = st.sidebar.slider("History points", 30, 500, 120)

st.sidebar.divider()
st.sidebar.subheader("AI advisor")
ai_on = st.sidebar.toggle("Enable AI advisor", value=True)
language = st.sidebar.selectbox("Advice language", ["English", "Tamil"])
auto_secs = st.sidebar.slider("Auto-refresh advice (s)", 30, 300, 90)
ask_now = st.sidebar.button("Ask AI now")
st.sidebar.caption("Key found" if ai.API_KEY else "No API key: using built-in rules")

if st.sidebar.button("Clear history"):
    ss.history, ss.alerts, ss.step = [], [], 0
    ss.advice, ss.advice_time, ss.advice_risk = None, 0.0, None
    st.rerun()

st.title("🌡️ Heat-Stress Early Warning Dashboard")

# ---------- read data ----------
reading, error, online = None, None, None
try:
    if demo:
        reading = bc.demo_reading(ss.step)
        online = True
    else:
        online = bc.is_device_online()
        reading = bc.read_all()
except Exception as e:
    error = str(e)

if error:
    st.error(f"Could not read from Blynk: {error}")
elif reading:
    ss.step += 1
    now = datetime.now()
    ss.history.append({"time": now.strftime("%H:%M:%S"), **reading})
    ss.history = ss.history[-keep:]

# ---------- dashboard display ----------
if ss.history:
    latest = ss.history[-1]
    risk = latest.get("risk", "NORMAL")
    action = latest.get("action", "CONTINUE WORK")
    color = COLORS.get(risk, "#1b9e4b")

    # Risk Banner
    st.markdown(
        f"""
        <div style="background-color: {color}; padding: 20px; border-radius: 10px; text-align: center; color: white;">
            <h3 style="margin: 0; font-size: 18px; letter-spacing: 2px;">{risk}</h3>
            <h1 style="margin: 10px 0 0 0; font-size: 36px; font-weight: bold;">{action}</h1>
        </div>
        """,
        unsafe_allow_html=True,
    )

    status_txt = "Device online · " + ("DEMO DATA" if demo else "LIVE") if online else "Device offline"
    st.caption(f"{'🟢' if online else '🔴'} {status_txt}")

    # Metrics row
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("BPM", latest.get("bpm", 0))
    col2.metric("Baseline", latest.get("baseline", 0))
    col3.metric("Deviation", latest.get("deviation", 0))
    col4.metric("Trend", latest.get("trend", "STABLE"))
    col5.metric("Temp °C", latest.get("temp", 0.0))

    # ---------- PHASE 2: AI ADVISOR CARD INTEGRATION ----------
    if ai_on:
        now_ts = time.time()
        risk_changed = (risk != ss.advice_risk)
        time_elapsed = (now_ts - ss.advice_time) > auto_secs

        if ask_now or ss.advice is None or risk_changed or time_elapsed:
            with st.spinner("🤖 AI Advisor is analyzing worker telemetry..."):
                ss.advice = ai.get_advice(ss.history, language=language)
                ss.advice_time = now_ts
                ss.advice_risk = risk

        a = ss.advice
        if a:
            st.markdown("---")
            st.subheader("🤖 Cloud AI Advisor (Claude)")
            st.info(a.get("summary", ""))

            col_a, col_b = st.columns(2)
            with col_a:
                st.markdown("**Why risk is changing**")
                for r in a.get("reasons", []):
                    st.markdown(f"- {r}")
            with col_b:
                st.markdown("**What to do**")
                for r in a.get("actions", []):
                    st.markdown(f"- {r}")
            if a.get("watch_for"):
                st.markdown(f"**Watch for:** {a['watch_for']}")
            st.caption(
                f"Source: {a.get('source', 'AI')} · updated {a.get('at', '')}"
                + (f" · {a['note']}" if a.get("note") else "")
                + " · Advisory only. The device decision above always applies."
            )

    # ---------- CHARTS & ALERTS ----------
    df = pd.DataFrame(ss.history).set_index("time")
    left, right = st.columns(2)
    left.subheader("BPM vs personal baseline")
    left.altair_chart(chart(df, ["bpm", "baseline"]), use_container_width=True)
    right.subheader("Ambient temperature")
    right.altair_chart(chart(df, ["temperature"]), use_container_width=True)

    st.subheader("Alert log")
    if risk in ["CAUTION", "HIGH WARNING"]:
        if not ss.alerts or ss.alerts[0]["time"] != latest["time"]:
            ss.alerts.insert(0, {"time": latest["time"], "risk": risk, "action": action, "bpm": latest.get("bpm"), "temp": latest.get("temp")})
    
    if ss.alerts:
        st.dataframe(pd.DataFrame(ss.alerts), use_container_width=True, hide_index=True)
    else:
        st.write("No alerts yet.")

    st.caption("Decision-support aid only. Not a medical device. Limits are prototype parameters that need calibration.")

time.sleep(refresh)
st.rerun()