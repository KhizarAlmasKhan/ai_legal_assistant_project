# telegram_bot.py
import os
import fitz  # PyMuPDF
import google.generativeai as genai
import requests
from bs4 import BeautifulSoup
import re
from telegram import (
    Update,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
    ConversationHandler,
)

# Set your Gemini API key here
os.environ["GEMINI_API_KEY"] = "AIzaSyBb0yOnYLBoicKe8SEajKCeMxqqAzneyzI"
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

FEATURES = [
    "1. PDF Question Answering",
    "2. PDF Summarization",
    "3. Basic Chatbot",
    "4. Legal Drafter",
    "5. Case Finder",
]

user_pdf_texts = {}  # Store user PDFs' text by user_id

# Legal Drafter states
(
    LD_DOC_TYPE,
    LD_COLLECTING_INPUTS,
) = range(2)

# Store user drafting data temporarily
user_legal_data = {}

# Templates for required fields per doc type
LEGAL_DOC_FIELDS = {
    "Will": [
        ("date", "Please enter the date of the will (e.g. 2025-06-03):"),
        ("full_name", "Please enter the full name of the testator:"),
        ("address", "Please enter the testator's address:"),
        ("beneficiaries", "Please enter the beneficiaries (comma separated names):"),
        ("executor", "Please enter the executor's name:"),
        ("executor_address", "Please enter the executor's address:"),
        ("guardian", "Please enter the guardian's name (or type 'None'):"),
        ("witness1", "Please enter witness 1's name:"),
        ("witness1_address", "Please enter witness 1's address:"),
        ("witness2", "Please enter witness 2's name:"),
        ("witness2_address", "Please enter witness 2's address:"),
        ("governing_law", "Please enter the governing law jurisdiction (e.g. California, USA):"),
    ],
    "Contract": [
        ("date", "Please enter the effective date of the contract (e.g. 2025-06-03):"),
        ("party_a", "Please enter Party A's name:"),
        ("party_a_state", "Please enter Party A's state or jurisdiction:"),
        ("party_a_address", "Please enter Party A's address:"),
        ("party_a_signatory", "Please enter Party A's signatory name:"),
        ("party_a_title", "Please enter Party A's signatory title:"),
        ("party_b", "Please enter Party B's name:"),
        ("party_b_state", "Please enter Party B's state or jurisdiction:"),
        ("party_b_address", "Please enter Party B's address:"),
        ("party_b_signatory", "Please enter Party B's signatory name:"),
        ("party_b_title", "Please enter Party B's signatory title:"),
        ("purpose", "Please enter the purpose of the contract:"),
        ("duration", "Please enter the duration of the contract:"),
        ("payment_terms", "Please enter the payment terms:"),
        ("dispute_resolution", "Please enter dispute resolution terms (or type 'None'):"),
        ("witness_name", "Please enter witness name (or type 'None'):"),
        ("governing_law", "Please enter the governing law jurisdiction (e.g. California, USA):"),
    ],
    "Rental Agreement": [
        ("date", "Please enter the date of the rental agreement (e.g. 2025-06-03):"),
        ("landlord_name", "Please enter the landlord's full name:"),
        ("tenant_name", "Please enter the tenant's full name:"),
        ("property_address", "Please enter the property address:"),
        ("rent_amount", "Please enter the rent amount (e.g. $1200):"),
        ("rent_due_date", "Please enter the rent due date each month (e.g. 1st of each month):"),
        ("security_deposit", "Please enter the security deposit amount:"),
        ("maintenance_responsibility", "Please specify maintenance responsibilities:"),
        ("use_of_property", "Please specify permitted use of the property:"),
        ("termination_clause", "Please specify termination conditions:"),
        ("governing_law", "Please enter the governing law jurisdiction (e.g. California, USA):"),
    ],
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = "Hi and welcome to AI Legal Assistant!\nPlease select a feature from below:\n\n"
    welcome_text += "\n".join(FEATURES)

    keyboard = [[feature] for feature in FEATURES]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

    await update.message.reply_text(welcome_text, reply_markup=reply_markup)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text

    # If currently in Legal Drafter conversation, let that handler take control
    if context.user_data.get('in_legal_draft_flow'):
        # Pass control to the conversation handler automatically
        return

    if text == FEATURES[0]:  # PDF Question Answering
        await update.message.reply_text("Please send me the PDF file you want to ask questions about.")
        context.user_data['awaiting_pdf'] = True
        context.user_data['pdf_loaded'] = False
        context.user_data['feature'] = 'qa'
        return

    if text == FEATURES[1]:  # PDF Summarization
        await update.message.reply_text("Please send me the PDF file you want summarized.")
        context.user_data['awaiting_pdf'] = True
        context.user_data['pdf_loaded'] = False
        context.user_data['feature'] = 'summarize'
        return

    if text == FEATURES[2]:  # Basic Chatbot
        await update.message.reply_text("You can now chat with me. Send me any message!")
        context.user_data['awaiting_pdf'] = False
        context.user_data['pdf_loaded'] = False
        context.user_data['feature'] = 'chatbot'
        return

    if text == FEATURES[3]:  # Legal Drafter selected
        context.user_data['in_legal_draft_flow'] = True
        # Start Legal Drafter conversation
        keyboard = [["Will", "Contract", "Rental Agreement"]]
        await update.message.reply_text(
            "You selected Legal Drafter.\nPlease choose the type of document you want to draft:",
            reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True),
        )
        return LD_DOC_TYPE

    if text == FEATURES[4]:  # Case Finder
        await update.message.reply_text(
            "🔍 Welcome to Case Finder!\n\n"
            "Send me a legal query or case details you want to search for, and I'll find relevant cases from Indian Kanoon.\n\n"
            "Example queries:\n"
            "• 'Article 21 right to life'\n"
            "• 'Contract breach damages'\n"
            "• 'Property dispute'\n"
            "• 'Criminal defamation'\n\n"
            "What case would you like to search for?"
        )
        context.user_data['awaiting_pdf'] = False
        context.user_data['pdf_loaded'] = False
        context.user_data['feature'] = 'case_finder'
        return

    # If user already loaded PDF for QA or Summarization
    if context.user_data.get('awaiting_pdf') and not context.user_data.get('pdf_loaded', False):
        await update.message.reply_text("Waiting for your PDF file. Please send it as a document.")
        return

    if context.user_data.get('pdf_loaded'):
        pdf_text = user_pdf_texts.get(user_id, "")
        if not pdf_text:
            await update.message.reply_text("PDF text not found. Please send the PDF again.")
            context.user_data['awaiting_pdf'] = True
            context.user_data['pdf_loaded'] = False
            return

        feature = context.user_data.get('feature', 'qa')

        try:
            if feature == 'qa':
                # User message is question
                answer = await get_answer_from_gemini(text, pdf_text)
                await update.message.reply_text(answer)
            elif feature == 'summarize':
                summary = await get_summary_from_gemini(pdf_text)
                await update.message.reply_text(summary)
            else:
                await update.message.reply_text("This feature is under development.")
        except Exception as e:
            await update.message.reply_text(f"Sorry, there was an error processing your request: {e}")
        return

    # If feature is chatbot, respond directly
    if context.user_data.get('feature') == 'chatbot':
        try:
            reply = await get_chatbot_response(text)
            await update.message.reply_text(reply)
        except Exception as e:
            await update.message.reply_text(f"Sorry, I encountered an error: {e}")
        return

    # If feature is case finder, search for cases
    if context.user_data.get('feature') == 'case_finder':
        try:
            await update.message.reply_text("🔍 Searching for cases... Please wait.")
            cases = await search_cases(text)
            
            if not cases:
                await update.message.reply_text(
                    "❌ No cases found for your query. Please try different keywords or be more specific."
                )
                return
            
            response = f"🔍 Found {len(cases)} relevant cases:\n\n"
            
            for i, case in enumerate(cases, 1):
                response += f"{i}. {case['title']}\n"
                if case.get('date'):
                    response += f"📅 Date: {case['date']}\n"
                if case.get('citation'):
                    response += f"📋 Citation: {case['citation']}\n"
                if case.get('articles'):
                    response += f"📜 Articles: {', '.join(case['articles'])}\n"
                response += f"📝 Summary: {case['summary']}\n"
                response += f"🔗 URL: {case['url']}\n\n"
                
                # Split long messages
                if len(response) > 3500:
                    await update.message.reply_text(response, parse_mode='Markdown')
                    response = ""
            
            if response:
                await update.message.reply_text(response, parse_mode='Markdown')
                
        except Exception as e:
            await update.message.reply_text(f"Sorry, I encountered an error while searching: {e}")
        return

    # If none matched
    if text in FEATURES:
        await update.message.reply_text(f"You selected: {text}\n(This feature is under development.)")
    else:
        await update.message.reply_text("Please select a feature from the given options by clicking a button.")


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    if not context.user_data.get('awaiting_pdf'):
        await update.message.reply_text("Please select the PDF Question Answering or Summarization feature first by typing /start and choosing the option.")
        return

    doc = update.message.document
    if doc.mime_type != 'application/pdf':
        await update.message.reply_text("Please send a valid PDF file.")
        return

    # Download the PDF file
    file = await context.bot.get_file(doc.file_id)
    file_path = f"{user_id}_uploaded.pdf"
    await file.download_to_drive(file_path)

    # Extract text from PDF
    text = extract_text_from_pdf(file_path)
    if not text.strip():
        await update.message.reply_text("Sorry, I couldn't extract any text from this PDF. Please try another file.")
        return

    user_pdf_texts[user_id] = text
    context.user_data['awaiting_pdf'] = False
    context.user_data['pdf_loaded'] = True

    await update.message.reply_text(
        "PDF successfully loaded! Now you can ask me questions about it or request the summary."
    )

    # Clean up the downloaded file
    try:
        os.remove(file_path)
    except Exception:
        pass


def extract_text_from_pdf(file_path):
    text = ""
    try:
        doc = fitz.open(file_path)
        for page in doc:
            text += page.get_text()
        doc.close()
    except Exception as e:
        print(f"Error extracting PDF text: {e}")
    return text


async def get_answer_from_gemini(question, pdf_text):
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')

        prompt = (
            f"You are an AI legal assistant. Answer the following question based on the provided PDF content:\n\n"
            f"PDF Content:\n{pdf_text}\n\nQuestion: {question}\n\n"
            f"Please provide a clear and accurate answer based on the content above."
        )

        response = model.generate_content(prompt)
        return response.text

    except Exception as e:
        print(f"Error getting response from Gemini: {e}")
        return f"Sorry, I encountered an error while processing your question: {str(e)}"


async def get_summary_from_gemini(pdf_text):
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')

        prompt = (
            f"You are an AI legal assistant. Summarize the following PDF content clearly and concisely:\n\n"
            f"{pdf_text}\n\nSummary:"
        )

        response = model.generate_content(prompt)
        return response.text

    except Exception as e:
        print(f"Error getting summary from Gemini: {e}")
        return f"Sorry, I encountered an error while summarizing the PDF: {str(e)}"


async def get_chatbot_response(message):
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"You are a helpful AI legal assistant. Respond to the following message: {message}"
        
        response = model.generate_content(prompt)
        return response.text

    except Exception as e:
        print(f"Error getting chatbot response: {e}")
        return "Sorry, I encountered an error while chatting."


# Case Finder Functions
async def search_cases(query, max_results=5):
    """Search Indian Kanoon for cases"""
    try:
        url = f"https://indiankanoon.org/search/?formInput={query.replace(' ', '+')}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
        }

        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        results = soup.select('div.result')

        cases = []

        for i, result in enumerate(results[:max_results]):
            title_element = result.select_one('div.result_title > a')
            if not title_element:
                continue

            title = title_element.get_text(strip=True)
            link = "https://indiankanoon.org" + title_element['href']

            # Try multiple preview sources
            preview_element = result.select_one('div.result_text') or result.select_one('p') or result
            preview = preview_element.get_text(strip=True) if preview_element else "Preview not available"

            if len(preview) > 300:
                preview = preview[:300] + "..."

            # Extract date and citation
            date_match = re.search(r'(\d{1,2}[-/]\d{1,2}[-/]\d{4}|\d{4})', title + " " + preview)
            date = date_match.group(1) if date_match else None

            citation_match = re.search(r'(\d{4}\s+\w+\s+\d+|\(\d{4}\)\s+\d+\s+\w+)', title + " " + preview)
            citation = citation_match.group(1) if citation_match else None

            articles = re.findall(r'Article\s+(\d+)', title + " " + preview, re.IGNORECASE)

            case_data = {
                "title": title,
                "url": link,
                "preview": preview,
                "date": date,
                "citation": citation,
                "articles": articles,
                "summary": f"Case related to {query}" + (f" - {preview[:100]}..." if preview else "")
            }

            cases.append(case_data)

        return cases

    except Exception as e:
        print(f"❌ Error searching Indian Kanoon: {e}")
        return []


### Legal Drafter Conversation Handlers ###

async def legal_doc_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc_type = update.message.text
    if doc_type not in LEGAL_DOC_FIELDS:
        await update.message.reply_text(
            "Please select a valid document type from the options: Will, Contract, Rental Agreement."
        )
        return LD_DOC_TYPE

    context.user_data['legal_doc_type'] = doc_type
    context.user_data['legal_responses'] = {}
    context.user_data['legal_field_index'] = 0

    # Ask the first question for this doc type
    field_key, question = LEGAL_DOC_FIELDS[doc_type][0]
    await update.message.reply_text(question)
    return LD_COLLECTING_INPUTS


async def legal_collect_inputs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_response = update.message.text
    doc_type = context.user_data['legal_doc_type']
    idx = context.user_data['legal_field_index']
    field_key, question = LEGAL_DOC_FIELDS[doc_type][idx]

    # Save the user's response for this field
    context.user_data['legal_responses'][field_key] = user_response

    # Move to next field
    idx += 1
    if idx >= len(LEGAL_DOC_FIELDS[doc_type]):
        # All inputs collected, generate draft
        await update.message.reply_text("Generating your legal document draft...")

        # Generate the document draft using Gemini API
        draft = await generate_legal_draft(doc_type, context.user_data['legal_responses'])

        await update.message.reply_text(draft, reply_markup=ReplyKeyboardRemove())

        # Reset legal draft flow
        context.user_data['in_legal_draft_flow'] = False
        context.user_data.pop('legal_doc_type', None)
        context.user_data.pop('legal_responses', None)
        context.user_data.pop('legal_field_index', None)
        return ConversationHandler.END
    else:
        # Ask next question
        context.user_data['legal_field_index'] = idx
        next_field_key, next_question = LEGAL_DOC_FIELDS[doc_type][idx]
        await update.message.reply_text(next_question)
        return LD_COLLECTING_INPUTS


async def generate_legal_draft(doc_type, inputs):
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')

        # Build prompt for the legal draft
        prompt_intro = (
            f"You are an expert legal drafter. Using the details below, generate a clear, "
            f"professional, and legally appropriate {doc_type}.\n\n"
        )

        # Format the inputs nicely
        details = "\n".join(f"{key.replace('_', ' ').capitalize()}: {value}" for key, value in inputs.items())

        prompt = f"{prompt_intro}{details}\n\nPlease draft the full {doc_type} document text below:\n"

        response = model.generate_content(prompt)
        return response.text

    except Exception as e:
        print(f"Error generating legal draft: {e}")
        return f"Sorry, I encountered an error generating the legal draft: {str(e)}"


async def legal_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Legal drafting cancelled.", reply_markup=ReplyKeyboardRemove()
    )
    context.user_data['in_legal_draft_flow'] = False
    return ConversationHandler.END


def main():
    application = ApplicationBuilder().token("7606492825:AAEZo-LO2RQITlsuqq3Xy9hc7MsxkqKaAqY").build()

    # Conversation handler for Legal Drafter
    legal_drafter_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('^4. Legal Drafter$'), legal_doc_type)],
        states={
            LD_DOC_TYPE: [MessageHandler(filters.Regex('^(Will|Contract|Rental Agreement)$'), legal_doc_type)],
            LD_COLLECTING_INPUTS: [MessageHandler(filters.TEXT & (~filters.COMMAND), legal_collect_inputs)],
        },
        fallbacks=[CommandHandler('cancel', legal_cancel)],
        allow_reentry=True,
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(legal_drafter_conv)
    application.add_handler(MessageHandler(filters.Document.PDF, handle_document))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    print("Bot is running...")
    application.run_polling()


if __name__ == '__main__':
    main()