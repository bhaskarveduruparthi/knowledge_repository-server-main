import re
import json
import requests
from datetime import datetime, timedelta
from sqlalchemy import func, extract
from models.repository_model import KNR, Modules, Domain, Sector
from default_settings import db

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3.2:3b"

VALID_DIMENSIONS = {'user', 'module', 'domain', 'sector', 'customer'}
VALID_PERIODS = {'day', 'week', 'month', 'quarter', 'year', 'all'}

DIMENSION_FIELD_MAP = {
    'user': KNR.username,
    'module': KNR.module_name,
    'domain': KNR.domain,
    'sector': KNR.sector,
    'customer': KNR.customer_name,
}

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
    if not extracted_value:
        return None
    cleaned = re.sub(r'\bmodule\b', '', extracted_value, flags=re.IGNORECASE)
    cleaned = re.sub(r'\bthe\b', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'[^a-z0-9\s]', '', cleaned.lower()).strip()
    if not cleaned:
        return None
    for valid_module in VALID_MODULES:
        code_part = valid_module.split(':')[0].strip().lower()
        if cleaned == code_part or code_part in cleaned or cleaned in valid_module.lower():
            return valid_module
    return None


# ── Rule-based extraction for things regex handles more reliably than an LLM ──

def extract_top_n(query: str):
    match = re.search(r'\btop\s+(\d+)\b', query.lower())
    if match:
        n = int(match.group(1))
        return max(1, min(n, 100))  # clamp to a sane range
    return None


def extract_period(query: str) -> str:
    q = query.lower()
    if re.search(r'\b(today|daily|this day)\b', q):
        return 'day'
    if re.search(r'\b(this week|weekly|past week|last week)\b', q):
        return 'week'
    if re.search(r'\b(this month|monthly|past month|last month)\b', q):
        return 'month'
    if re.search(r'\b(this quarter|quarterly|past quarter|last quarter)\b', q):
        return 'quarter'
    if re.search(r'\b(this year|yearly|annual|past year|last year)\b', q):
        return 'year'
    return 'all'


# ── LLM extraction for the fuzzier parts: mode, group_by, filters ──

def extract_report_spec(query: str) -> dict:
    prompt = f"""Extract a report specification from this request. Respond with ONLY valid JSON, exactly one object, no other text.

Fields:
- mode: "aggregate" if asking for counts, totals, "top", "most", "breakdown", or "how many" grouped by something.
         "list" if asking to show/see/find the actual solutions/records themselves.
- group_by: ONLY used when mode is "aggregate". Array of the dimension(s) being counted/ranked: user, module, domain, sector, customer.
  IMPORTANT: include EVERY dimension implied by the question, not just the one after "by".
  Examples:
    "top contributors" -> group_by: ["user"]
    "who uploaded the most solutions by domain" -> group_by: ["domain", "user"]  (BOTH "who"=user AND "by domain"=domain)
    "which customer has the most solutions by domain" -> group_by: ["domain", "customer"]  (BOTH dimensions)
    "breakdown by module" -> group_by: ["module"]  (only one dimension implied)
- filters: object with module/domain/sector/customer/user — ONLY if a SPECIFIC NAMED value is mentioned (like "FLM" or "Accenture India").
  NEVER put a generic word like "all", "any", or the dimension name itself as a filter value.
  "by domain" alone (with no specific domain named) means NO filter — only use it as a group_by dimension.

Request: {query}

JSON:"""

    response = requests.post(OLLAMA_URL, json={
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        "options": {"num_predict": 150, "temperature": 0.0}
    })
    response.raise_for_status()
    raw = response.json()["response"].strip()
    if raw.startswith("```"):
        raw = raw.strip("`").replace("json", "", 1).strip()

    try:
        decoder = json.JSONDecoder()
        parsed, _ = decoder.raw_decode(raw)
    except json.JSONDecodeError:
        parsed = {}

    if not isinstance(parsed, dict):
        parsed = {}

    mode = parsed.get('mode') if parsed.get('mode') in ('aggregate', 'list') else None
    group_by = parsed.get('group_by', [])
    if not isinstance(group_by, list):
        group_by = []
    group_by = [g for g in group_by if g in VALID_DIMENSIONS]

    if mode is None:
        mode = 'aggregate' if group_by else 'list'

    raw_filters = parsed.get('filters', {})
    if not isinstance(raw_filters, dict):
        raw_filters = {}

    # Defensive validation — reject filter values that are clearly not real, specific names
    GENERIC_NOISE_VALUES = {'all', 'any', 'every', 'each', 'unknown', 'none', '',
                              'user', 'module', 'domain', 'sector', 'customer'}

    filters = {}
    module_mentioned_but_unresolved = False

    if raw_filters.get('module'):
        resolved = resolve_module_name(raw_filters['module'])
        if resolved:
            filters['module'] = resolved
        else:
            module_mentioned_but_unresolved = True

    for key in ('domain', 'sector', 'customer', 'user'):
        value = raw_filters.get(key)
        if value and str(value).strip().lower() not in GENERIC_NOISE_VALUES:
            filters[key] = str(value).strip()

    top_n = extract_top_n(query)
    period = extract_period(query)

    return {
        "mode": mode,
        "group_by": group_by,
        "filters": filters,
        "period": period,
        "top_n": top_n,
        "module_mentioned_but_unresolved": module_mentioned_but_unresolved
    }


# ── Period filtering ──────────────────────────────────────────────────────

def apply_period_filter(query, model_field, period):
    now = datetime.utcnow()
    if period == 'day':
        return query.filter(model_field >= now - timedelta(days=1))
    elif period == 'week':
        return query.filter(model_field >= now - timedelta(weeks=1))
    elif period == 'month':
        return query.filter(extract('year', model_field) == now.year, extract('month', model_field) == now.month)
    elif period == 'quarter':
        qstart = ((now.month - 1) // 3) * 3 + 1
        return query.filter(
            extract('year', model_field) == now.year,
            extract('month', model_field) >= qstart,
            extract('month', model_field) < qstart + 3
        )
    elif period == 'year':
        return query.filter(extract('year', model_field) == now.year)
    return query  # 'all' — no filter


def apply_dimension_filters(query, filters):
    if filters.get('module'):
        query = query.filter(KNR.module_name == filters['module'])
    if filters.get('domain'):
        query = query.filter(KNR.domain.ilike(f"%{filters['domain']}%"))
    if filters.get('sector'):
        query = query.filter(KNR.sector.ilike(f"%{filters['sector']}%"))
    if filters.get('customer'):
        query = query.filter(KNR.customer_name.ilike(f"%{filters['customer']}%"))
    if filters.get('user'):
        query = query.filter(KNR.username.ilike(f"%{filters['user']}%"))
    return query


# ── Query execution ───────────────────────────────────────────────────────

def run_aggregate_report(group_by, filters, period, top_n):
    if not group_by:
        group_by = ['user']  # sensible default for "top contributors"-style requests with no explicit dimension

    fields = [DIMENSION_FIELD_MAP[g].label(g) for g in group_by]
    base = db.session.query(*fields, func.count(KNR.id).label('count')) \
        .filter(KNR.Approval_status == 'Approved')

    base = apply_dimension_filters(base, filters)
    base = apply_period_filter(base, KNR.created_at, period)
    base = base.group_by(*[DIMENSION_FIELD_MAP[g] for g in group_by]) \
        .order_by(func.count(KNR.id).desc())

    if top_n:
        base = base.limit(top_n)

    results = base.all()
    data = [dict(zip(group_by + ['count'], row)) for row in results]

    if not data:
        return data, "No matching data found for that breakdown."

    group_label = " / ".join(group_by)
    lines = [f"{i+1}. " + " | ".join(str(row[g]) for g in group_by) + f" — {row['count']}" for i, row in enumerate(data)]
    answer = f"Breakdown by {group_label}:\n" + "\n".join(lines)
    return data, answer


def run_list_report(filters, period, top_n):
    query = KNR.query.filter_by(Approval_status='Approved')
    query = apply_dimension_filters(query, filters)
    query = apply_period_filter(query, KNR.created_at, period)
    if top_n:
        query = query.limit(top_n)

    results = query.all()
    data = [{
        "id": r.id, "customer_name": r.customer_name, "module_name": r.module_name,
        "domain": r.domain, "sector": r.sector, "username": r.username
    } for r in results]

    answer = f"Found {len(data)} approved solution(s)" + (" matching your filters." if filters or period != 'all' else ".")
    return data, answer


def run_report(query: str):
    spec = extract_report_spec(query)

    if spec.get('module_mentioned_but_unresolved'):
        return [], "I couldn't match that to a known module name. Could you specify it more precisely?", spec

    if spec['mode'] == 'aggregate':
        data, answer = run_aggregate_report(spec['group_by'], spec['filters'], spec['period'], spec['top_n'])
    else:
        data, answer = run_list_report(spec['filters'], spec['period'], spec['top_n'])

    return data, answer, spec

def extract_explicit_module_mention(query: str):
    """Backup extraction: catches '<word> module' patterns directly via regex,
    independent of whether the LLM noticed and extracted it as a filter."""
    match = re.search(r'\b([a-zA-Z]+)\s+module\b', query, re.IGNORECASE)
    if match:
        candidate = match.group(1)
        if candidate.lower() not in ('the', 'a', 'this', 'that', 'any', 'every', 'each', 'which', 'what'):
            return candidate
    return None