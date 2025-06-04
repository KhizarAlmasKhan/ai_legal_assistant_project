import os
import tempfile
import traceback
from flask import Blueprint, request, jsonify
from pdf2image import convert_from_path
import pytesseract
from google.generativeai import configure, GenerativeModel
from langdetect import detect

pdfqa_bp = Blueprint('pdfqa_bp', __name__)

# Set your Gemini API key from environment variable
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
configure(api_key=GOOGLE_API_KEY)

model = GenerativeModel('gemini-1.5-flash')

def extract_text_from_pdf(pdf_path):
    images = convert_from_path(pdf_path)
    text = ""
    for i, img in enumerate(images):
        try:
            img_text = pytesseract.image_to_string(img)
            text += f"\n--- Page {i+1} ---\n{img_text.strip()}"
        except Exception as e:
            text += f"\n--- Page {i+1} ---\n[OCR Failed: {str(e)}]"
    return text

@pdfqa_bp.route("/api/pdf-qa", methods=["POST"])
def pdf_qa():
    try:
        file = request.files.get("file")
        question = request.form.get("question", "").strip()

        if not file or not question:
            return jsonify({"error": "File and question are required"}), 400

        # Save PDF to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
            file.save(tmp_pdf.name)
            extracted_text = extract_text_from_pdf(tmp_pdf.name)

        # Detect language for prompt adaptation (optional)
        try:
            lang = detect(question)
        except:
            lang = "en"

        prompt = f"""You are a legal assistant AI. Based on the following document content, answer the user's question.

Document Content:
\"\"\"
{extracted_text[:20000]}  # limit text for token cap
\"\"\"

Question: {question}
Answer:"""

        response = model.generate_content(prompt)
        answer = response.text.strip()

        return jsonify({"answer": answer})

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": f"Server error: {str(e)}"}), 500
