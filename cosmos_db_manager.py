"""
Cosmos DB Manager for Vector Search and Document Storage
Replaces Pinecone with Azure Cosmos DB for MongoDB vCore
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import numpy as np
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure
import hashlib

logger = logging.getLogger(__name__)

class CosmosDBManager:
    """Manages Cosmos DB connection and vector operations"""
    
    def __init__(self, connection_string: str, database_name: str = "document_chatbot", collection_name: str = "documents"):
        self.connection_string = connection_string
        self.database_name = database_name
        self.collection_name = collection_name
        self.client = None
        self.database = None
        self.collection = None
        self._initialize_cosmos_db()
    
    def _initialize_cosmos_db(self):
        """Initialize Cosmos DB connection and create collections if needed"""
        try:
            # Connect to Cosmos DB
            self.client = MongoClient(self.connection_string)
            
            # Test connection
            self.client.admin.command('ping')
            logger.info("Successfully connected to Cosmos DB")
            
            # Get database and collection
            self.database = self.client[self.database_name]
            self.collection = self.database[self.collection_name]
            
            # Create vector search index if it doesn't exist
            self._ensure_vector_index()
            
        except ConnectionFailure as e:
            logger.error(f"Failed to connect to Cosmos DB: {e}")
            raise
        except Exception as e:
            logger.error(f"Error initializing Cosmos DB: {e}")
            raise
    
    def _ensure_vector_index(self):
        """Create vector search index for embeddings"""
        try:
            # Check if vector index exists
            indexes = list(self.collection.list_indexes())
            vector_index_exists = any(
                index.get('name') == 'vector_index' 
                for index in indexes
            )
            
            if not vector_index_exists:
                # Create vector search index using MongoDB command for Cosmos DB vCore
                vector_index_command = {
                    "createIndexes": self.collection_name,
                    "indexes": [
                        {
                            "name": "vector_index",
                            "key": {
                                "embedding": "cosmosSearch"
                            },
                            "cosmosSearchOptions": {
                                "kind": "vector-ivf",
                                "numLists": 1,
                                "similarity": "COS",
                                "dimensions": 3072
                            }
                        }
                    ]
                }
                
                # Execute the command on the database
                result = self.database.command(vector_index_command)
                logger.info(f"Created vector search index: {result}")
            else:
                logger.info("Vector search index already exists")
                
        except Exception as e:
            logger.warning(f"Could not create vector index: {e}")
            # Continue without vector index - basic functionality will still work
    
    def upsert_document(self, doc_id: str, text: str, embedding: List[float], metadata: Dict[str, Any]):
        """Insert or update a document with its embedding"""
        try:
            document = {
                "_id": doc_id,
                "text": text,
                "embedding": embedding,
                "metadata": metadata,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            # Use upsert operation
            result = self.collection.replace_one(
                {"_id": doc_id},
                document,
                upsert=True
            )
            
            if result.upserted_id:
                logger.debug(f"Inserted new document: {doc_id}")
            else:
                logger.debug(f"Updated existing document: {doc_id}")
                
            return True
            
        except Exception as e:
            logger.error(f"Error upserting document {doc_id}: {e}")
            return False
    
    def batch_upsert_documents(self, documents: List[Dict[str, Any]]):
        """Batch upsert multiple documents for efficiency"""
        try:
            operations = []
            for doc in documents:
                doc_id = doc.get('id') or self._generate_doc_id(doc['text'], doc['metadata'])
                
                # Validate embedding dimensions
                embedding = doc['embedding']
                if len(embedding) != 3072:
                    logger.error(f"Embedding dimension mismatch: expected 3072, got {len(embedding)}")
                    continue
                
                document = {
                    "_id": doc_id,
                    "text": doc['text'],
                    "embedding": embedding,
                    "metadata": doc['metadata'],
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
                
                operations.append({
                    "replaceOne": {
                        "filter": {"_id": doc_id},
                        "replacement": document,
                        "upsert": True
                    }
                })
            
            if operations:
                result = self.collection.bulk_write(operations)
                logger.info(f"Batch upserted {len(operations)} documents. "
                          f"Inserted: {result.upserted_count}, Modified: {result.modified_count}")
                return True
            
        except Exception as e:
            logger.error(f"Error in batch upsert: {e}")
            return False
    
    def vector_search(self, query_embedding: List[float], top_k: int = 10, 
                     filter_dict: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Perform vector similarity search"""
        try:
            # Try vector search first
            try:
                # Build aggregation pipeline for vector search
                pipeline = []
                
                # Vector search stage for Cosmos DB vCore
                vector_search_stage = {
                    "$search": {
                        "cosmosSearch": {
                            "vector": query_embedding,
                            "path": "embedding",
                            "k": top_k
                        }
                    }
                }
                
                # Add filter if provided
                if filter_dict:
                    vector_search_stage["$search"]["cosmosSearch"]["filter"] = filter_dict
                
                pipeline.append(vector_search_stage)
                
                # Add score projection
                pipeline.append({
                    "$project": {
                        "text": 1,
                        "metadata": 1,
                        "score": {"$meta": "searchScore"},
                        "_id": 1
                    }
                })
                
                # Execute search
                results = list(self.collection.aggregate(pipeline))
                
            except Exception as vector_error:
                logger.warning(f"Vector search failed, falling back to manual similarity: {vector_error}")
                return self._fallback_text_search(query_embedding, top_k, filter_dict)
            
            # Format results
            formatted_results = []
            for result in results:
                formatted_results.append({
                    'id': str(result['_id']),
                    'text': result['text'],
                    'metadata': result['metadata'],
                    'score': result.get('score', 0.0)
                })
            
            logger.debug(f"Vector search returned {len(formatted_results)} results")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error in vector search: {e}")
            # Fallback to text search if vector search fails
            return self._fallback_text_search(query_embedding, top_k, filter_dict)
    
    def _fallback_text_search(self, query_embedding: List[float], top_k: int, 
                             filter_dict: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Fallback text-based search when vector search is not available"""
        try:
            # Simple text search as fallback
            query = {}
            if filter_dict:
                query.update(filter_dict)
            
            # Get all documents and compute similarity manually
            documents = list(self.collection.find(query).limit(top_k * 5))
            
            if not documents:
                return []
            
            # Compute cosine similarity manually
            results_with_scores = []
            query_vector = np.array(query_embedding)
            
            for doc in documents:
                if 'embedding' in doc and doc['embedding']:
                    doc_vector = np.array(doc['embedding'])
                    
                    # Cosine similarity
                    similarity = np.dot(query_vector, doc_vector) / (
                        np.linalg.norm(query_vector) * np.linalg.norm(doc_vector)
                    )
                    
                    results_with_scores.append({
                        'id': str(doc['_id']),
                        'text': doc['text'],
                        'metadata': doc['metadata'],
                        'score': float(similarity)
                    })
            
            # Sort by similarity and return top_k
            results_with_scores.sort(key=lambda x: x['score'], reverse=True)
            return results_with_scores[:top_k]
            
        except Exception as e:
            logger.error(f"Error in fallback search: {e}")
            return []
    
    def delete_documents(self, filter_dict: Dict[str, Any]):
        """Delete documents matching the filter"""
        try:
            result = self.collection.delete_many(filter_dict)
            logger.info(f"Deleted {result.deleted_count} documents with filter: {filter_dict}")
            return result.deleted_count
        except Exception as e:
            logger.error(f"Error deleting documents: {e}")
            return 0
    
    def get_document_count(self, filter_dict: Optional[Dict] = None) -> int:
        """Get count of documents matching filter"""
        try:
            if filter_dict:
                return self.collection.count_documents(filter_dict)
            else:
                return self.collection.estimated_document_count()
        except Exception as e:
            logger.error(f"Error getting document count: {e}")
            return 0
    
    def list_documents(self, filter_dict: Optional[Dict] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """List documents with metadata only"""
        try:
            query = filter_dict or {}
            cursor = self.collection.find(
                query, 
                {"metadata": 1, "_id": 1, "created_at": 1}
            ).limit(limit)
            
            documents = []
            for doc in cursor:
                documents.append({
                    'id': str(doc['_id']),
                    'metadata': doc['metadata'],
                    'created_at': doc.get('created_at')
                })
            
            return documents
            
        except Exception as e:
            logger.error(f"Error listing documents: {e}")
            return []
    
    def _generate_doc_id(self, text: str, metadata: Dict[str, Any]) -> str:
        """Generate a unique document ID based on content and metadata"""
        content = f"{text[:100]}{json.dumps(metadata, sort_keys=True)}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def reset_collection_for_new_embeddings(self):
        """Reset collection when changing embedding models"""
        try:
            # Drop the collection to remove all documents and indexes
            self.collection.drop()
            logger.info("Dropped collection for embedding model change")
            
            # Recreate collection and indexes
            self.collection = self.database[self.collection_name]
            self._ensure_vector_index()
            logger.info("Recreated collection with new embedding dimensions")
            
        except Exception as e:
            logger.error(f"Error resetting collection: {e}")
    
    def close_connection(self):
        """Close the database connection"""
        try:
            if self.client:
                self.client.close()
                logger.info("Closed Cosmos DB connection")
        except Exception as e:
            logger.error(f"Error closing connection: {e}")
    
    def __del__(self):
        """Cleanup on object destruction"""
        self.close_connection()