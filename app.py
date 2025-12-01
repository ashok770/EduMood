import os
import json
import csv
import time
import datetime
from io import StringIO
from dotenv import load_dotenv

import google.generativeai as genai
from flask import Flask, request, jsonify, render_template, make_response

# Load env variables
load_dotenv()

app = Flask(__name__)

# API Key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in environment variables.")

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(model_name="gemini-2.5-flash")

# Emotion categories
EMOTION_CATEGORIES = [
    "Happy/Engaged",
    "Neutral/Calm",
    "Confused",
    "Bored/Drowsy",
    "Frustrated/Stressed"
]

DATA_FILE = 'data.json'


# ------------------ Utility Functions ------------------

def load_data():
    if not os.path.exists(DATA_FILE) or os.path.getsize(DATA_FILE) == 0:
        return []
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return []


def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)


def classify_emotion_gemini(text):
    try:
        prompt = (
            f"Analyze the student feedback: \"{text}\".\n"
            f"Choose one emotion from this list: {EMOTION_CATEGORIES}.\n"
            "Respond in JSON with: emotion, reasoning."
        )

        response = model.generate_content(
            prompt,
            generation_config={
                "response_mime_type": "application/json"
            }
        )

        return json.loads(response.text), 200

    except Exception as e:
        return {"error": str(e)}, 500


# ------------------ ROUTES ------------------

@app.route('/')
@app.route('/home')
def home():
    return render_template('home.html')


@app.route('/submit_feedback')
def index():
    return render_template('student_feedback.html')


@app.route('/about')
def about():
    return render_template('about_me.html')


@app.route('/submit_feedback', methods=['POST'])
def submit_feedback():
    feedback_text = request.form.get('feedback', '').strip()

    if not feedback_text:
        return jsonify({"error": "Empty feedback."}), 400

    result, status = classify_emotion_gemini(feedback_text)
    if status != 200:
        return jsonify(result), status

    all_data = load_data()
    entry = {
        "timestamp": int(time.time()),
        "feedback": feedback_text,
        "emotion": result["emotion"],
        "reasoning": result["reasoning"]
    }

    all_data.append(entry)
    save_data(all_data)

    return jsonify(entry), 200


@app.route('/dashboard')
def dashboard():
    return render_template('teacher_dashboard.html', feedback_data=load_data())


@app.route('/download_csv')
def download_csv():
    all_data = load_data()
    if not all_data:
        return "No data available.", 404

    fieldnames = ["timestamp", "feedback", "emotion", "reasoning"]

    si = StringIO()
    cw = csv.DictWriter(si, fieldnames=fieldnames)
    cw.writeheader()
    cw.writerows(all_data)

    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=EduMood_Data.csv"
    output.headers["Content-type"] = "text/csv"
    return output


@app.route('/api/time_series_data')
def time_series_data():
    all_data = load_data()
    if not all_data:
        return jsonify([])

    daily = {}

    for entry in all_data:
        date_str = datetime.datetime.fromtimestamp(entry["timestamp"]).strftime('%Y-%m-%d')

        if date_str not in daily:
            daily[date_str] = {"negative": 0, "total": 0}

        daily[date_str]["total"] += 1

        if entry["emotion"] in ["Confused", "Frustrated/Stressed", "Bored/Drowsy"]:
            daily[date_str]["negative"] += 1

    result = []
    for d, c in sorted(daily.items()):
        index = c["negative"] / c["total"]
        result.append({
            "date": d,
            "confusion_index": round(index, 3)
        })

    return jsonify(result)


# ---------- MAIN ----------
if __name__ == '__main__':
    app.run(debug=True)
