import requests

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