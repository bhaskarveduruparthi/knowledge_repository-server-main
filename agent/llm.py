import requests
import json

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3.2:3b"

def generate_answer(query, context_chunks):
    if not context_chunks:
        return "I don't have relevant information about that in the knowledge repository."

    context_text = "\n\n".join(
        f"[Source {i+1}] {chunk['text']}" for i, chunk in enumerate(context_chunks)
    )

    prompt = f"""You are a helpful assistant for a Knowledge Repository system.
Answer the user's question using ONLY the information in the context below.

CRITICAL RULE 1: Do not invent, assume, or add any technical detail, transaction code, BAdI name, configuration step, or specific procedure that is not explicitly written in the context below.

CRITICAL RULE 2: When listing Technical Details, copy ALL items exactly as they appear in the context, separated by commas. Do not drop any item.

CRITICAL RULE 3: Format your answer EXACTLY like this template, with each line starting with a dash, and Customer and Module on SEPARATE lines (never combine them):

- Requirement: <what the requirement solves, one sentence>
- Technical Details: <copy all items exactly from context>
- Customer Benefit: <copy as stated in context>
- Customer: <customer name only>
- Module: <module name only>

If configuration steps are not present in the context, do not add a line for them — just omit it.

Context:
{context_text}

Question: {query}

Answer (follow the exact template above, no deviations):"""
    response = requests.post(OLLAMA_URL, json={
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        "options": {
            "num_predict": 400,
            "temperature": 0.1
        }
    })
    response.raise_for_status()
    return response.json()["response"]

def summarize_text(text: str) -> str:
    # Truncate to a safe size — local 3B models slow down significantly and lose
    # coherence on very long inputs. ~6000 characters is a practical ceiling here.
    MAX_CHARS = 6000
    truncated = len(text) > MAX_CHARS
    text_to_summarize = text[:MAX_CHARS]

    prompt = f"""Summarize the following document in 4-6 clear sentences.
Focus on the main purpose, key points, and any important conclusions or action items.
Do not add information that isn't in the document.

Document:
{text_to_summarize}

Summary:"""

    response = requests.post(OLLAMA_URL, json={
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        "options": {
            "num_predict": 300,
            "temperature": 0.2
        }
    })
    response.raise_for_status()
    summary = response.json()["response"]

    if truncated:
        summary += "\n\n(Note: this document was long — summary is based on the first portion only.)"

    return summary




VALID_MODULES = [
    'FI: Financial Accounting', 'CO: Controlling', 'MM: Materials Management',
    'SD: Sales and Distribution', 'HCM: Human Capital Management', 'PP: Production Planning',
    'PM: Plant Maintenance', 'QM: Quality Management', 'PS: Project System',
    'FSCM: Financial Supply Chain Management', 'SRM: Supplier Relationship Management',
    'CRM: Customer Relationship Management', 'LE: Logistics Execution', 'WM: Warehouse Management',
    'EWM: Extended Warehouse Management', 'TRM: Treasury and Risk Management', 'FM: Funds Management',
    'IM: Investment Management', 'PLM: Product Lifecycle Management',
    'BI/BW: Business Intelligence / Business Warehouse', 'GRC: Governance, Risk, and Compliance',
    'MDM: Master Data Management', 'EHS: Environment, Health, and Safety',
    'SEM: Strategic Enterprise Management', 'BASIS: SAP Basis (technical administration)',
    'ABAP: Advanced Business Application Programming (development)',
    'PI/XI: Process Integration / Exchange Infrastructure (middleware)', 'EP: Enterprise Portal',
    'SOLMAN: SAP Solution Manager', 'Fiori: SAP Fiori (UX and apps)', 'FLM: File Lifecycle Management',
    'CPI: Cloud Platform Integration', 'BTP: Business Technology Platform', 'AI: Artificial Intelligence',
    'Cloud ALM: Cloud Application Lifecycle Management', 'API: Application Programming Interface',
    'SAC: SAP Analytics Cloud', 'Python: Python Programming Language',
    'Salesforce: Salesforce Customer 360 Platform'
]

def resolve_module_name(extracted_value):
    """Matches a loosely-extracted module reference against the real module list using Python."""
    if not extracted_value:
        return None

    # Strip common noise words the LLM might include
    cleaned = extracted_value.strip().lower()
    for noise_word in ['module', 'the ', ' the']:
        cleaned = cleaned.replace(noise_word, '').strip()

    for valid_module in VALID_MODULES:
        code_part = valid_module.split(':')[0].strip().lower()
        if cleaned == code_part or cleaned in valid_module.lower() or code_part in cleaned:
            return valid_module

    return None


def extract_search_filters(query: str) -> dict:
    """Lightweight extraction — no large lists in the prompt, just simple free-text fields.
    Module resolution to the real, valid string happens separately, in Python."""

    prompt = f"""Extract any filters mentioned in this request. Respond with ONLY valid JSON, nothing else — exactly one JSON object, no extra text.

Fields (omit any not clearly mentioned):
- module: short module name or abbreviation if mentioned (e.g. "FI", "Materials Management")
- customer: customer/company name if mentioned
- domain: industry domain if mentioned
- sector: sector if mentioned

If nothing is mentioned, respond with exactly: {{}}

Request: {query}

JSON:"""

    response = requests.post(OLLAMA_URL, json={
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        "options": {"num_predict": 100, "temperature": 0.0}
    })
    response.raise_for_status()
    raw = response.json()["response"].strip()

    if raw.startswith("```"):
        raw = raw.strip("`").replace("json", "", 1).strip()

    # Defensive: only take the FIRST JSON object if the model produces extra text after it
    try:
        decoder = json.JSONDecoder()
        parsed, _ = decoder.raw_decode(raw)
    except json.JSONDecodeError:
        return {}

    if not isinstance(parsed, dict):
        return {}

    if parsed.get('module'):
       
        resolved = resolve_module_name(parsed['module'])

        print(f"[FILTER DEBUG] Extracted: {repr(parsed['module'])} → Resolved: {repr(resolved)}")
        if resolved:
            parsed['module'] = resolved
        else:
            del parsed['module']  # couldn't confidently resolve it — drop rather than guess
            

    # Drop any empty-string values the model might still produce
    return {k: v for k, v in parsed.items() if v}