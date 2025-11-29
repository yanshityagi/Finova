# Tools/mongo_tools.py

import pandas as pd
from pymongo import MongoClient
import os

def get_mongo_client():
    """
    Returns a MongoDB Atlas client using MONGODB_URI from .env
    """
    uri = os.getenv("MONGODB_URI")
    if not uri:
        raise ValueError("MONGODB_URI not found in .env")
    return MongoClient(uri, tls=True, tlsAllowInvalidCertificates=True)


def insert_transactions(db_name: str, collection_name: str, transactions: list):
    """
    Inserts parsed transactions into Atlas.
    """
    print ("inserting txns")
    client = get_mongo_client()
    db = client[db_name]
    collection = db[collection_name]

    if not transactions:
        return {"status": "error", "message": "No transactions to insert"}

    result = collection.insert_many(transactions)

    return {
        "status": "success",
        "inserted_count": len(result.inserted_ids),
        "collection": collection_name
    }


def list_transactions(db_name: str, collection_name: str, limit=5):
    """
    Fetches a few sample transactions.
    """
    client = get_mongo_client()
    db = client[db_name]
    collection = db[collection_name]

    return list(collection.find().limit(limit))

def save_uploaded_info(filename: str, txn_count: int) -> bool:
    # Save upload info
    client = get_mongo_client()
    db = client[os.getenv("FINOVA_DB_NAME")]
    col = db["transactions"]
    
    uploads_col = db["uploaded_files"]
    uploads_col.insert_one({
        "filename": filename,
        "uploaded_at": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
        "transaction_count": txn_count,
        "bank_name": "User Upload"
    })