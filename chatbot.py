# chatbot.py
from flask import Blueprint, request, jsonify
import google.generativeai as genai
import os

chatbot_bp = Blueprint('chatbot', __name__)
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Configure Gemini 2.5 Flash
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

@chatbot_bp.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        question = data.get("question", "").strip()

        if not question:
            return jsonify({"error": "Question is required."}), 400

        prompt = f"You are a helpful legal assistant. Answer in clear and simple terms.\n\nQuestion: {question}"
        response = model.generate_content(prompt)

        if response and response.text:
            return jsonify({"answer": response.text.strip()})
        else:
            return jsonify({"error": "No response generated."}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500
