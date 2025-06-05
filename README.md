# ⚖️ AI Legal Assistant

A smart, AI-powered web application that simplifies legal information access and drafting. Users can upload legal PDFs to get clear summaries, ask context-specific questions, interact with a general-purpose legal chatbot, draft documents, find Indian legal case references, and even access these features through Telegram.

---

## 🚀 Key Features

- 📄 **PDF Summarizer**  
  Upload any legal document and receive a clear, section-wise summary with extracted key clauses (e.g., termination, liability, confidentiality).

- ❓ **PDF-Based Q&A**  
  Ask natural language questions about an uploaded PDF and get instant, accurate answers grounded in the document’s content.

- 💬 **General Legal Chatbot**  
  Get answers to legal concepts in simple language using a conversational AI trained for legal assistance.

- 📜 **Legal Document Drafter**  
  Instantly generate professional legal documents (e.g., NDA, Contract, Will, Lease) by filling simple form inputs — all drafted using Gemini 2.5 Flash.

- 🔍 **Legal Case Finder**  
  Search Indian Kanoon for real legal cases by topic or article (e.g., “Article 21 right to life”, “contract breach damages”) and view citations, previews, and full-text summaries.

- 🤖 **Telegram Bot Interface**  
  Use all core features via Telegram with a user-friendly chat interface — including file uploads, legal Q&A, summaries, drafting, and case searching.

- 🎥 **Legal Awareness Blog**  
  Browse educational legal videos to learn about rights, laws, real-world cases, and justice systems in practice.

---

## 🧠 Tech Stack

| Technology              | Purpose                                                         |
|--------------------------|-----------------------------------------------------------------|
| **Flask**               | Backend API for all routes                                      |
| **HTML + TailwindCSS**  | Clean, responsive frontend UI                                   |
| **Google Gemini 2.5 Flash** | Unified AI model powering all core features                   |
| **Tesseract OCR**       | Extracts text from scanned/image-based PDF pages                |
| **LangDetect**          | Filters out non-English pages from legal PDFs                   |
| **BeautifulSoup4**      | Scrapes Indian Kanoon for legal case data                       |
| **Telegram Bot API**    | Provides mobile-friendly chatbot for legal help via Telegram    |

---

## 🗂️ Project Structure

| File/Folder         | Purpose                                                        |
|---------------------|----------------------------------------------------------------|
| `app.py`            | Main Flask app that registers all feature blueprints           |
| `chatbot.py`        | Gemini-powered chatbot endpoint for `/chat`                    |
| `pdf_qa.py`         | Handles `/api/pdf-qa` endpoint for file-based legal Q&A        |
| `summary.py`        | Summarizes legal PDFs and extracts clauses using Gemini        |
| `legal_drafter.py`  | Drafts documents like NDAs, Wills, Contracts via structured prompts |
| `case_finder.py`    | Scrapes Indian Kanoon and handles `/find-cases` endpoint       |
| `telegram_bot.py`   | Telegram integration for all core AI features                  |
| `.env`              | Environment variables (API keys) — excluded from GitHub        |
| `requirements.txt`  | Python dependencies (Flask, Gemini, LangChain, etc.)           |
| `templates/`        | HTML templates rendered by Flask                               |
| ├── `index.html`    | Homepage with feature overview                                 |
| ├── `blog.html`     | Legal awareness video content                                  |
| ├── `pdf-summary.html` | UI for uploading PDFs and getting summaries                  |
| ├── `pdf-qa.html`   | UI for file-based Q&A                                           |
| ├── `legal-chat.html` | UI for general-purpose legal chatbot                          |
| `static/`           | CSS, JS, icons, and other frontend assets                      |
| `pdfs/`             | Temporary PDF uploads (ignored in GitHub)                      |
| `vectorstore/`      | (Optional) Embedding store if FAISS or LangChain used          |

---

## 🛠️ To Run

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set up your .env file
# Example:
# GOOGLE_API_KEY=your_gemini_api_key
# TELEGRAM_TOKEN=your_telegram_bot_token

# 3. Run Flask backend
python app.py

# 4. Run Telegram bot (optional)
python telegram_bot.py
