from flask import Blueprint, request, jsonify
import os
import fitz  # PyMuPDF
import google.generativeai as genai
from dotenv import load_dotenv

# Load .env and configure Gemini
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

summary_bp = Blueprint("summary", __name__)

# Load Gemini model
model = genai.GenerativeModel("models/gemini-1.5-flash")

@summary_bp.route("/summarize", methods=["POST"])
def summarize_pdf():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]

    if not file.filename.endswith(".pdf"):
        return jsonify({"error": "Only PDF files are supported"}), 400

    # Read text from PDF
    try:
        doc = fitz.open(stream=file.read(), filetype="pdf")
        text = "\n".join([page.get_text() for page in doc])
    except Exception as e:
        return jsonify({"error": "Failed to read PDF"}), 500

    # Gemini prompt
    prompt = f"""
    You are a legal assistant. Summarize the following legal document in simple language.
    Also, extract any important clauses or sections, and return them separately.
    
    Document:
    {text[:10000]}  # Limit characters to avoid Gemini overload
    """

    try:
        response = model.generate_content(prompt)
        output = response.text

        # Simple parsing (customize based on Gemini output)
        summary_text, clauses = output.split("Important Clauses", 1)
        clauses_lines = clauses.strip().split("\n")
        clause_dict = {}

        for line in clauses_lines:
            if ":" in line:
                key, val = line.split(":", 1)
                clause_dict[key.strip()] = [v.strip() for v in val.split(";")]

        return jsonify({
            "summary": summary_text.strip(),
            "clauses": clause_dict
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500
