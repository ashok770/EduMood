import os
import json
import csv
from io import StringIO # Needed for creating a CSV in memory
from dotenv import load_dotenv

from google import genai
from google.genai.errors import APIError
from flask import Flask, request, jsonify, render_template, redirect, url_for, make_response

# Load environment variables
load_dotenv()

# --- Configuration & Initialization ---

# 🌟 CRITICAL: Flask App Instance MUST be defined before any @app.route()
app = Flask(__name__) 

# Get API Key or raise error
# Assuming you use GEMINI_API_KEY from your .env file
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found. Please create a .env file and add your key.")

# Initialize the Gemini Client
# It automatically picks up the API key from the environment
try:
    client = genai.Client()
except Exception as e:
    # Log error if client fails to initialize (e.g., if key is invalid)
    print(f"Error initializing Gemini Client: {e}")
    client = None


# Define the structured set of emotions
EMOTION_CATEGORIES = [
    "Happy/Engaged",
    "Neutral/Calm",
    "Confused",
    "Bored/Drowsy",
    "Frustrated/Stressed"
]

DATA_FILE = 'data.json'

# --- Utility Functions ---

def load_data():
    """
    Reads all stored feedback from the JSON file.
    Robustly handles empty or missing files.
    """
    # Check if the file is missing or empty (size == 0)
    if not os.path.exists(DATA_FILE) or os.path.getsize(DATA_FILE) == 0:
        return []
    
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            # Handle case where file might be corrupted after initialization
            app.logger.warning(f"Warning: Corrupt JSON in {DATA_FILE}. Returning empty list.")
            return []


def save_data(data):
    """Writes the updated feedback list back to the JSON file."""
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)


def classify_emotion_gemini(feedback_text):
    """
    Sends feedback to Gemini for structured emotion classification.
    """
    if not client:
        return {"error": "AI client not initialized (check API key)."}, 500
        
    system_instruction = (
        "You are an expert NLP classifier for educational feedback. "
        "Your task is to analyze the following student comment about a class or lecture "
        "and strictly choose the single best-fitting emotion from the allowed list."
    )

    user_prompt = (
        f"Analyze the student feedback: \"{feedback_text}\". "
        f"Based on the tone and content, select the single best emotion from the "
        f"following list: {EMOTION_CATEGORIES}."
    )

    response_schema = {
        "type": "OBJECT",
        "properties": {
            "emotion": {
                "type": "STRING",
                "enum": EMOTION_CATEGORIES,
                "description": "The single best emotion that describes the student's feedback."
            },
            "reasoning": {
                "type": "STRING",
                "description": "A short, one-sentence justification for the chosen emotion."
            }
        },
        "required": ["emotion", "reasoning"]
    }

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=user_prompt,
            config={
                'system_instruction': system_instruction,
                'response_mime_type': 'application/json',
                'response_schema': response_schema,
            }
        )
        return json.loads(response.text), 200

    except APIError as e:
        app.logger.error(f"Gemini API Error: {e}")
        return {"error": "AI service temporarily unavailable."}, 503
    except Exception as e:
        app.logger.error(f"Unexpected Error: {e}")
        return {"error": "An unexpected error occurred during processing."}, 500


# --- Flask Routes ---

@app.route('/')
def index():
    """Renders the main student feedback submission page."""
    return render_template('student_feedback.html')

@app.route('/submit_feedback', methods=['POST'])
def submit_feedback():
    """
    Handles form submission, calls the AI, stores the data, and returns the result.
    """
    feedback_text = request.form.get('feedback', '').strip()

    if not feedback_text:
        return jsonify({"error": "No feedback text provided."}), 400

    # 1. Classify Emotion
    emotion_result, status_code = classify_emotion_gemini(feedback_text)
    
    if status_code != 200:
        return jsonify(emotion_result), status_code

    # 2. Store Data
    all_data = load_data()
    # Use current time for timestamp, not file creation time
    new_entry = {
        "timestamp": os.path.getctime(DATA_FILE), 
        "feedback": feedback_text,
        "emotion": emotion_result['emotion'],
        "reasoning": emotion_result['reasoning']
    }
    all_data.append(new_entry)
    save_data(all_data)

    return jsonify(new_entry), 200


@app.route('/dashboard')
def dashboard():
    """Renders the teacher dashboard with all the analytics."""
    all_data = load_data()
    # Pass all raw data to the template for JS/Chart.js processing
    return render_template('teacher_dashboard.html', feedback_data=all_data)


@app.route('/download_csv')
def download_csv():
    """
    Retrieves all stored data, converts it to CSV format, and sends it for download.
    """
    all_data = load_data()

    if not all_data:
        return "No data available to download.", 404

    # The field names (CSV headers) must match the keys in your data
    fieldnames = ["timestamp", "feedback", "emotion", "reasoning"]

    # Use StringIO to build the CSV file in memory 
    si = StringIO()
    cw = csv.DictWriter(si, fieldnames=fieldnames)
    
    # 1. Write the column headers
    cw.writeheader()
    
    # 2. Write the data rows
    cw.writerows(all_data)

    # 3. Create a Flask response object with the CSV data
    output = make_response(si.getvalue())
    
    # 4. Set the necessary headers to force the browser to download a CSV file
    output.headers["Content-Disposition"] = "attachment; filename=EduMood_Feedback_Data.csv"
    output.headers["Content-type"] = "text/csv"
    
    return output


# --- Run the App ---
if __name__ == '__main__':
    app.run(debug=True)