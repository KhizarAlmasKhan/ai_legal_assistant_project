# legal_drafter.py
from flask import Blueprint, request, jsonify
import google.generativeai as genai
import os

drafter_bp = Blueprint('drafter', __name__)
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")

@drafter_bp.route('/draft', methods=['POST'])
def draft():
    data = request.get_json()
    print("🔍 Received data:", data)

    doc_type = data.get("type")
    inputs = data.get("inputs")

    if not doc_type or not inputs:
        return jsonify({"error": "Document type and inputs are required."}), 400

    try:
        prompt = get_prompt(doc_type, inputs)
        print("🧠 Prompt sent to Gemini:\n", prompt)
        response = model.generate_content(prompt)
        return jsonify({"document": response.text})
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        print("❌ Error generating document:", e)
        return jsonify({"error": str(e)}), 500


def get_prompt(doc_type, inputs):
    if doc_type == "nda":
        return f"""
Draft a comprehensive Non-Disclosure Agreement with the following details:

- Date: {inputs['date']}
- Party A: {inputs['party_a']} ({inputs['party_a_state']}), located at {inputs['party_a_address']}
  Signatory: {inputs['party_a_signatory']}, Title: {inputs['party_a_title']}
- Party B: {inputs['party_b']} ({inputs['party_b_state']}), located at {inputs['party_b_address']}
  Signatory: {inputs['party_b_signatory']}, Title: {inputs['party_b_title']}
- Purpose: {inputs['purpose']}
- Duration: {inputs['duration']} years
- Governing Law: {inputs['governing_law']}
- Witness (optional): {inputs.get('witness_name', 'None provided')}

Include standard NDA clauses: definition of confidential information, obligations, exclusions, term, termination, remedies, and governing law.
"""

    elif doc_type == "lease":
        return f"""
Create a residential Lease Agreement with the following inputs:

- Effective Date: {inputs['date']}
- Landlord: {inputs['landlord']}, Address: {inputs['landlord_address']}
- Tenant: {inputs['tenant']}, Address: {inputs['tenant_address']}
- Property Address: {inputs['property_address']}
- Term: {inputs['lease_term']}
- Monthly Rent: {inputs['monthly_rent']}, Due: {inputs['rent_due']}
- Security Deposit: {inputs['security_deposit']}
- Late Fee Policy: {inputs['late_fee']}
- Utilities Responsibility: {inputs['utilities']}
- Governing Law: {inputs['governing_law']}

Include standard sections for use of property, maintenance, early termination, and signatures.
"""

    elif doc_type == "will":
        return f"""
Draft a Last Will and Testament using the following details:

- Date: {inputs['date']}
- Testator: {inputs['full_name']}, Address: {inputs['address']}
- Beneficiaries: {inputs['beneficiaries']}
- Executor: {inputs['executor']}, Address: {inputs['executor_address']}
- Guardian (optional): {inputs.get('guardian', 'None provided')}
- Witness 1: {inputs['witness1']}, Address: {inputs['witness1_address']}
- Witness 2: {inputs['witness2']}, Address: {inputs['witness2_address']}
- Governing Law: {inputs['governing_law']}

Include clauses for asset distribution, appointment of executor, guardian (if applicable), and witness signatures.
"""

    elif doc_type == "contract":
        return f"""
Generate a formal business Contract using the following inputs:

- Effective Date: {inputs['date']}
- Party A: {inputs['party_a']} ({inputs['party_a_state']}), Address: {inputs['party_a_address']}
  Signatory: {inputs['party_a_signatory']}, Title: {inputs['party_a_title']}
- Party B: {inputs['party_b']} ({inputs['party_b_state']}), Address: {inputs['party_b_address']}
  Signatory: {inputs['party_b_signatory']}, Title: {inputs['party_b_title']}
- Purpose: {inputs['purpose']}
- Duration: {inputs['duration']}
- Payment Terms: {inputs['payment_terms']}
- Dispute Resolution: {inputs.get('dispute_resolution', 'Not specified')}
- Witness (optional): {inputs.get('witness_name', 'None provided')}
- Governing Law: {inputs['governing_law']}

Include essential sections like definitions, scope, responsibilities, liabilities, dispute resolution, termination, and signatures.
"""

    else:
        raise ValueError("Unsupported document type.")