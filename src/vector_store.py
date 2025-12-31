
from pymongo import MongoClient
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from src.config import Config
from src.utils import setup_logging

logger = setup_logging(__name__)

class VectorStore:
    """Manages interactions with Azure Cosmos DB for Vector Search"""
    
    def __init__(self):
        self.client = None
        self.collection = None
        self._connect()
        
    def _connect(self):
        """Establish connection to Cosmos DB"""
        try:
            self.client = MongoClient(Config.COSMOS_DB_CONNECTION_STRING)
            # Test connection
            self.client.admin.command('ping')
            
            db = self.client[Config.DB_NAME]
            self.collection = db[Config.COLLECTION_NAME]
            
            # Ensure index exists
            self._ensure_index()
            logger.info("✅ Connected to Cosmos DB Vector Store")
            
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            raise

    def _ensure_index(self):
        """Create vector search index if not exists"""
        try:
            # Check existing indexes using list_indexes()
            # Note: Implementation details may vary based on driver version, 
            # this is a standard MongoDB checks approach
            indexes = self.collection.list_indexes()
            index_exists = any(idx.get('name') == 'vector_index' for idx in indexes)
            
            if not index_exists:
                # Create the specific Cosmos DB vector index
                # Note: This command is specific to Azure Cosmos DB for MongoDB vCore
                command = {
                    "createIndexes": Config.COLLECTION_NAME,
                    "indexes": [{
                        "name": "vector_index",
                        "key": {"embedding": "cosmosSearch"},
                        "cosmosSearchOptions": {
                            "kind": "vector-ivf",
                            "numLists": 1,
                            "similarity": "COS",
                            "dimensions": Config.EMBEDDING_DIMENSION
                        }
                    }]
                }
                self.client[Config.DB_NAME].command(command)
                logger.info("Created new vector index")
                
        except Exception as e:
            logger.warning(f"Index creation check failed (might already exist): {e}")

    def add_documents(self, documents: List[Dict[str, Any]]) -> int:
        """
        Add documents to the store.
        Expected format: {'id': str, 'text': str, 'embedding': list, 'metadata': dict}
        """
        if not documents:
            return 0
            
        operations = []
        for doc in documents:
            # Prepare document for MongoDB
            mongo_doc = {
                "_id": doc['id'],
                "text": doc['text'],
                "embedding": doc['embedding'],
                "metadata": doc['metadata'],
                "created_at": datetime.utcnow()
            }
            
            # Use replace_one with upsert=True to handle updates
            from pymongo import ReplaceOne
            operations.append(ReplaceOne(
                {"_id": doc['id']},
                mongo_doc,
                upsert=True
            ))
            
        if operations:
            result = self.collection.bulk_write(operations)
            return len(documents)
        return 0

    def search(self, query_vector: List[float], limit: int = 5) -> List[Dict]:
        """
        Perform vector similarity search
        """
        try:
            pipeline = [
                {
                    "$search": {
                        "cosmosSearch": {
                            "vector": query_vector,
                            "path": "embedding",
                            "k": limit
                        },
                        "returnStoredSource": True
                    }
                },
                {
                    "$project": {
                        "text": 1,
                        "metadata": 1,
                        "score": {"$meta": "searchScore"}
                    }
                }
            ]
            
            results = list(self.collection.aggregate(pipeline))
            return results
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
            
    def delete_by_source(self, source_filename: str):
        """Delete all chunks belonging to a specific file"""
        result = self.collection.delete_many({"metadata.source": source_filename})
        return result.deleted_count
