import chromadb
from chromadb.utils import embedding_functions

import pymysql

DB_CONFIG = {
    "host": "10.6.102.245",
    "user": "admin",
    "password": "Saibhaskar9",
    "database": "knwldg_repository",
}

embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)
client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_or_create_collection(
    name="knr_documents",
    embedding_function=embedding_fn
)

def search_documents(query, n_results=5, filters=None, approval_status=None, max_distance=0.65):
    where_conditions = []

    if filters:
        if filters.get('module'):
            where_conditions.append({"module_name": {"$eq": filters['module']}})
        if filters.get('customer'):
            where_conditions.append({"customer_name": {"$eq": filters['customer']}})
        if filters.get('domain'):
            where_conditions.append({"domain": {"$eq": filters['domain']}})
        if filters.get('sector'):
            where_conditions.append({"sector": {"$eq": filters['sector']}})

    if approval_status:
        where_conditions.append({"approval_status": {"$eq": approval_status}})

    if len(where_conditions) > 1:
        where_filter = {"$and": where_conditions}
    elif len(where_conditions) == 1:
        where_filter = where_conditions[0]
    else:
        where_filter = None

    results = collection.query(
        query_texts=[query],
        n_results=n_results,
        where=where_filter
    )

    matches = []
    for doc, meta, distance in zip(
        results['documents'][0], results['metadatas'][0], results['distances'][0]
    ):
        if distance <= max_distance:
            matches.append({"text": doc, "metadata": meta, "distance": distance})
    return matches

def get_document_by_id(doc_id):
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    cursor.execute("SELECT * FROM knr WHERE id = %s", (doc_id,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return row