from flask import request
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from .extraction import extract_text_from_attachment
from .llm import generate_answer, summarize_text
from .retreival import search_documents
from models.user_model import User
from models.repository_model import KNR
from resources.repository_views import _serialize_with_access


class AgentSearch(Resource):
    def post(self):
        data = request.get_json()
        query = data.get('query')
        if not query:
            return {"error": "query is required"}, 400

        results = search_documents(query, n_results=5)
        return {"query": query, "results": results}


class AgentChat(Resource):
    def post(self):
        data = request.get_json()
        query = data.get('query')
        if not query:
            return {"error": "query is required"}, 400

        chunks = search_documents(query, n_results=3)
        answer = generate_answer(query, chunks)

        return {
            "query": query,
            "answer": answer,
            "sources": [c['metadata'] for c in chunks]
        }


class AgentDocument(Resource):
    @jwt_required()
    def get(self, doc_id):
        identity = get_jwt_identity()
        user = User.query.filter_by(yash_id=identity).first()
        if user is None:
            return {"error": "User not found"}, 401

        doc = KNR.query.get(doc_id)
        if doc is None:
            return {"error": "Document not found"}, 404

        # Reuses the exact same access logic as your main repos page —
        # correctly computes download_approved per-user, excludes the raw blob
        serialized = _serialize_with_access([doc], user)[0]
        return serialized
    


class AgentSummarize(Resource):
    @jwt_required()
    def post(self, doc_id):
        identity = get_jwt_identity()
        user = User.query.filter_by(yash_id=identity).first()
        if user is None:
            return {"error": "User not found"}, 401

        doc = KNR.query.get(doc_id)
        if doc is None:
            return {"error": "Document not found"}, 404

        if not doc.attachment_data:
            return {"error": "No attachment found for this document"}, 404

        text = extract_text_from_attachment(doc.attachment_data, doc.attachment_filename)
        if not text:
            return {"error": "Could not extract readable text from this file type. Supported: PDF, DOCX, TXT, CSV."}, 422

        summary = summarize_text(text)
        return {"summary": summary}