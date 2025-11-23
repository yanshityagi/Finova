from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

uri = os.getenv("MONGODB_URI")
print("URI:", uri)

client = MongoClient(uri, tls=True, tlsAllowInvalidCertificates=True)

try:
    print(client.list_database_names())
    print("SUCCESS: Connected!")
except Exception as e:
    print("ERROR:", e)
