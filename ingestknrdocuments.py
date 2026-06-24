import pymysql
import chromadb
from chromadb.utils import embedding_functions

# Fill in your actual MySQL credentials here
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "Saibhaskar9",
    "database": "knwldg_repository"
}

def get_documents():
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    cursor.execute("""
        SELECT id, customer_name, domain, sector, module_name,
               detailed_requirement, technical_details, customer_benefit,
               business_justification, Approval_status, username, user_id
        FROM knr
        WHERE LENGTH(detailed_requirement) > 15
    """)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows

def build_document_text(row):
    return f"""Customer: {row['customer_name']}
Module: {row['module_name']}
Requirement: {row['detailed_requirement']}
Technical Details: {row['technical_details']}
Customer Benefit: {row['customer_benefit']}
Business Justification: {row['business_justification'] or 'N/A'}""".strip()

def chunk_text(text, max_chars=800, overlap=100):
    """Split long text into overlapping pieces so we don't lose context at chunk boundaries."""
    if len(text) <= max_chars:
        return [text]
    chunks = []
    start = 0
    while start < len(text):
        end = start + max_chars
        chunks.append(text[start:end])
        start = end - overlap
    return chunks

# Set up ChromaDB (same as before, new collection name for real data)
embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)
client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_or_create_collection(
    name="knr_documents",
    embedding_function=embedding_fn
)

rows = get_documents()
print(f"Fetched {len(rows)} rows from MySQL")

ids, documents, metadatas = [], [], []

for row in rows:
    text = build_document_text(row)
    chunks = chunk_text(text)
    for i, chunk in enumerate(chunks):
        ids.append(f"doc{row['id']}_chunk{i}")
        documents.append(chunk)
        metadatas.append({
    "doc_id": row['id'],
    "customer_name": row['customer_name'],
    "module_name": row['module_name'],
    "domain": row['domain'],       # NEW
    "sector": row['sector'],       # NEW
    "approval_status": row['Approval_status'] or "Unknown",
    "owner_user_id": row['user_id'] or 0
})

collection.upsert(ids=ids, documents=documents, metadatas=metadatas)
print(f"Ingested {len(documents)} chunks into ChromaDB")