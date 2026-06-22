import chromadb
from chromadb.utils import embedding_functions

import pymysql

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
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

def search_documents(query, n_results=5, user_id=None, approval_status=None, max_distance=0.65):
    where_filter = {}
    if approval_status:
        where_filter["approval_status"] = approval_status

    results = collection.query(
        query_texts=[query],
        n_results=n_results,
        where=where_filter if where_filter else None
    )

    matches = []
    for doc, meta, distance in zip(
        results['documents'][0], results['metadatas'][0], results['distances'][0]
    ):
        if distance <= max_distance:
            matches.append({
                "text": doc,
                "metadata": meta,
                "distance": distance
            })
    return matches

def get_document_by_id(doc_id):
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    cursor.execute("SELECT * FROM knr WHERE id = %s", (doc_id,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return row