from flask import request
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity

from agent.reports import run_report
from .extraction import extract_text_from_attachment
from .llm import extract_search_filters, generate_answer, summarize_text
from .retreival import search_documents
from models.user_model import User
from models.repository_model import KNR
from resources.repository_views import _serialize_with_access
import re



class AgentSearch(Resource):
    def post(self):
        data = request.get_json()
        query = data.get('query')
        if not query:
            return {"error": "query is required"}, 400

        results = search_documents(query, n_results=8, max_distance=0.7)
        return {"query": query, "results": results}


class AgentChat(Resource):
    def post(self):
        data = request.get_json()
        query = data.get('query')
        if not query:
            return {"error": "query is required"}, 400

        filters = extract_search_filters(query)
        chunks = search_documents(query, n_results=3, filters=filters)
        answer = generate_answer(query, chunks)

        return {
            "query": query,
            "answer": answer,
            "sources": [c['metadata'] for c in chunks],
            "filters_applied": filters
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
    

class AgentReport(Resource):
    def post(self):
        data = request.get_json()
        query = data.get('query')
        if not query:
            return {"error": "query is required"}, 400

        q_lower = query.lower()
        if re.search(r'\b(list|show|what|which)\b.*\bmodules?\b', q_lower) and 'solution' not in q_lower:
            from models.repository_model import Modules
            modules = Modules.query.order_by(Modules.module_name).all()
            report_data = [{"module_name": m.module_name, "key_name": m.key_name} for m in modules]
            return {"query": query, "answer": f"There are {len(report_data)} modules configured.", "report_data": report_data, "downloadable": True}

        if re.search(r'\b(list|show|what|which)\b.*\bdomains?\b', q_lower) and 'solution' not in q_lower:
            from models.repository_model import Domain
            domains = Domain.query.order_by(Domain.name).all()
            report_data = [{"domain": d.name, "sector_count": len(d.sectors)} for d in domains]
            return {"query": query, "answer": f"There are {len(report_data)} domains.", "report_data": report_data, "downloadable": True}

        if re.search(r'\b(list|show|what|which)\b.*\bsectors?\b', q_lower) and 'solution' not in q_lower:
            from models.repository_model import Sector
            sectors = Sector.query.order_by(Sector.name).all()
            report_data = [{"sector": s.name, "domain": s.domain.name if s.domain else None} for s in sectors]
            return {"query": query, "answer": f"There are {len(report_data)} sectors.", "report_data": report_data, "downloadable": True}

        report_data, answer, spec = run_report(query)
        return {
            "query": query,
            "answer": answer,
            "report_data": report_data,
            "spec": spec,
            "downloadable": len(report_data) > 0
        }


class AgentReportExport(Resource):
    def post(self):
        import pandas as pd
        from io import BytesIO
        from flask import send_file

        data = request.get_json()
        report_data = data.get('report_data', [])
        if not report_data:
            return {"error": "No data to export"}, 400

        df = pd.DataFrame(report_data)
        output = BytesIO()
        df.to_excel(output, index=False, engine='openpyxl')
        output.seek(0)

        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            download_name='knr_report.xlsx',
            as_attachment=True
        )