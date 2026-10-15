import os
import json
import anthropic
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("ANTHROPIC_API_KEY")

def get_advice(history, language="English"):
    # If API key is missing or still has placeholder text, use fallback
    if not API_KEY or API_KEY.startswith("your_") or API_KEY == "":
        return fallback_advice(history, language)
    
    try:
        latest = history[-1] if history else {}
        risk = latest.get("risk", "NORMAL")
        bpm = latest.get("bpm", 75)
        baseline = latest.get("baseline", 74)
        temp = latest.get("temp", 32.0)
        
        client = anthropic.Anthropic(api_key=API_KEY)
        
        prompt = f"""
        You are an industrial heat-stress safety advisor. Analyze the current worker telemetry and respond with a valid JSON object ONLY (no extra markdown text outside the JSON) with these exact keys:
        - "summary": A brief one-sentence overview in {language}.
        - "reasons": A list of 2 short strings explaining why the risk is changing in {language}.
        - "actions": A list of 2-3 short actionable steps in {language}.
        - "watch_for": A short string of symptoms to monitor in {language}.
        - "source": Set to "Claude API".
        - "at": Current status update.

        Telemetry:
        - Risk State: {risk}
        - Current BPM: {bpm}
        - Baseline BPM: {baseline}
        - Temperature: {temp}°C
        """
        
        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=400,
            messages=[{"role": "user", "content": prompt}]
        )
        
        text = message.content[0].text.strip()
        
        # Clean up any potential markdown code block wrappers
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
            
        return json.loads(text)
        
    except Exception as e:
        # If API call fails for any reason, safely fall back to built-in rules
        return fallback_advice(history, language)

def fallback_advice(history, language="English"):
    latest = history[-1] if history else {}
    risk = latest.get("risk", "NORMAL")
    
    if language == "Tamil":
        if risk == "HIGH WARNING":
            return {
                "summary": "எச்சரிக்கை: கடுமையான வெப்ப அழுத்தம் கண்டறியப்பட்டுள்ளது.",
                "reasons": ["இதய துடிப்பு இயல்பை விட அதிகமாக உள்ளது.", "உடல் வெப்பநிலை உயர்ந்துள்ளது."],
                "actions": ["உடனடியாக வேலையை நிறுத்தவும்", "குளிர்ந்த நிழல் பகுதிக்கு செல்லவும்", "தண்ணீர் குடிக்கவும்"],
                "watch_for": "தலைசுற்றல் அல்லது மயக்கம்",
                "source": "Built-in Rules (Fallback)",
                "note": "Local device safety protocols take precedence."
            }
        elif risk == "CAUTION":
            return {
                "summary": "கவனம்: வெப்ப அழுத்தம் அதிகரித்து வருகிறது.",
                "reasons": ["இதய துடிப்பு சற்று உயர்ந்துள்ளது."],
                "actions": ["சிறிது நேரம் ஓய்வெடுக்கவும்", "தண்ணீர் அருந்தவும்"],
                "watch_for": "அதிகப்படியான வியர்வை",
                "source": "Built-in Rules (Fallback)"
            }
        else:
            return {
                "summary": "நிலைமை சீராக உள்ளது.",
                "reasons": ["அனைத்து அளவீடுகளும் பாதுகாப்பான வரம்பிற்குள் உள்ளன."],
                "actions": ["தொடர்ந்து பணிகளை மேற்கொள்ளலாம்"],
                "watch_for": "வழக்கமான சோர்வு",
                "source": "Built-in Rules (Fallback)"
            }
    else:
        if risk == "HIGH WARNING":
            return {
                "summary": "CRITICAL: Severe heat stress indicators detected.",
                "reasons": ["Heart rate significantly exceeds personal baseline.", "Thermal load is critical."],
                "actions": ["Stop work immediately", "Move to a shaded cooling area", "Hydrate with cool water"],
                "watch_for": "Dizziness, confusion, or nausea",
                "source": "Built-in Rules (Fallback)",
                "note": "Local device safety protocols take precedence."
            }
        elif risk == "CAUTION":
            return {
                "summary": "CAUTION: Rising metrics require attention.",
                "reasons": ["Elevated heart rate trend detected."],
                "actions": ["Take a short rest break", "Hydrate"],
                "watch_for": "Fatigue or heavy sweating",
                "source": "Built-in Rules (Fallback)"
            }
        else:
            return {
                "summary": "NORMAL: Worker telemetry is within safe parameters.",
                "reasons": ["Heart rate and temperature are stable."],
                "actions": ["Continue normal work rhythm"],
                "watch_for": "Regular hydration breaks",
                "source": "Built-in Rules (Fallback)"
            }
