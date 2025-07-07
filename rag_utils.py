import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

collection_name = "sensitive_terms"
client = None
collection = None

def init_chroma():
    global client, collection
    client = chromadb.PersistentClient(path="./chroma")
    embedding_func = SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")

    if collection_name not in [c.name for c in client.list_collections()]:
        collection = client.create_collection(name=collection_name, embedding_function=embedding_func)
    else:
        collection = client.get_collection(name=collection_name, embedding_function=embedding_func)

def is_similar_to_sensitive_db(word):
    results = collection.query(query_texts=[word], n_results=1)
    distances = results.get("distances", [])
    
    # Check if any results were returned
    if distances and len(distances[0]) > 0:
        return distances[0][0] < 0.3

    # No vectors in the DB yet
    return False


def add_to_sensitive_db(word):
    doc_id = f"{collection.count()}_{word}"
    collection.add(documents=[word], ids=[doc_id])
