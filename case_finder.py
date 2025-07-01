# case_finder.py

from flask import Blueprint, request, jsonify
import requests
from bs4 import BeautifulSoup
import re

case_finder_bp = Blueprint('case_finder', __name__)  # Fix: __name__ not _name_

def search_indian_kanoon(query, max_results=5):
    """Search Indian Kanoon directly for cases"""
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

            # Log when no preview is found
            if preview == "Preview not available":
                print(f"⚠️ No preview found for: {title}")

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

def get_case_full_text(case_url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
        }

        response = requests.get(case_url, headers=headers, timeout=15)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        case_text_div = (soup.find('div', id='maincontent') or 
                         soup.find('div', class_='doc_content') or 
                         soup.find('pre'))

        if case_text_div:
            return case_text_div.get_text(separator='\n', strip=True)[:2000]
        else:
            return "Full text not available"

    except Exception as e:
        print(f"❌ Error fetching case text: {e}")
        return "Full text not available"

@case_finder_bp.route('/find-cases', methods=['POST'])
def find_cases():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        query = data.get("query", "").strip()
        if not query:
            return jsonify({"error": "Query parameter is required"}), 400

        if len(query) > 200:
            return jsonify({"error": "Query too long (max 200 characters)"}), 400

        print(f"🔍 Searching Indian Kanoon for: {query}")

        cases = search_indian_kanoon(query, max_results=5)

        if not cases:
            print("❌ No cases found")
            return jsonify([])

        print(f"✅ Found {len(cases)} cases")

        # Try to enhance first case
        try:
            full_text = get_case_full_text(cases[0]['url'])
            if full_text and full_text != "Full text not available":
                cases[0]['full_text_preview'] = full_text
                if len(full_text) > 500:
                    cases[0]['summary'] = full_text[:400] + "..."
        except:
            pass

        return jsonify(cases)

    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return jsonify({"error": "Internal server error"}), 500

@case_finder_bp.route('/get-case-details', methods=['POST'])
def get_case_details():
    try:
        data = request.get_json()
        case_url = data.get('url', '').strip()

        if not case_url:
            return jsonify({"error": "Case URL required"}), 400

        if not case_url.startswith('https://indiankanoon.org'):
            return jsonify({"error": "Invalid Indian Kanoon URL"}), 400

        full_text = get_case_full_text(case_url)

        return jsonify({
            "url": case_url,
            "full_text": full_text,
            "status": "success"
        })

    except Exception as e:
        print(f"❌ Error getting case details: {e}")
        return jsonify({"error": "Failed to fetch case details"}), 500

@case_finder_bp.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "healthy",
        "service": "case_finder",
        "version": "1.0"
    })