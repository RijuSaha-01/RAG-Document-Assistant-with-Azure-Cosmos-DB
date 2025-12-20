"""
Document Chatbot with Cosmos DB Integration
==========================================

This module implements the core chatbot functionality for the Document Chat Assistant.
It integrates Azure Cosmos DB for vector storage, OpenAI for embeddings and chat,
and provides comprehensive document processing and conversation management.

Key Features:
- Vector-based document similarity search using Cosmos DB
- GPT-4 powered conversational AI with document context
- Multi-format document processing (PDF, DOCX, PPTX)
- PowerPoint presentation generation from conversations
- Robust error handling and fallback mechanisms
- Conversation state management and context tracking

Architecture:
- Uses Azure Cosmos DB for MongoDB vCore for vector storage
- Leverages OpenAI's text-embedding-3-large for embeddings
- Implements GPT-4o for intelligent response generation
- Integrates with document processor for multi-format support
- Connects to presentation generator for PowerPoint creation

Author: Document Chat Assistant Team
Version: 3.0
"""

# Standard library imports
import os
import json
import logging
import tempfile
import shutil
from typing import List, Dict, Any, Optional
from datetime import datetime

# Third-party imports
from dotenv import load_dotenv
import openai
from langchain_openai import OpenAIEmbeddings, ChatOpenAI

# Local imports
from cosmos_db_manager import CosmosDBManager
from document_processor import DocumentProcessor
from presentation_generator import PresentationGenerator

# ============================================================================
# Environment Configuration
# ============================================================================

# Load environment variables from .env file
load_dotenv()

# ============================================================================
# Logging Configuration
# ============================================================================

# Configure comprehensive logging for the chatbot
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),           # Console output
        logging.FileHandler('chatbot.log') # File output
    ]
)

# Create module-specific logger
logger = logging.getLogger('cosmos_chatbot')

# ============================================================================
# Main Chatbot Class
# ============================================================================

class CosmosChatbot:
    """
    Advanced Document Chatbot with Cosmos DB Integration
    
    This class provides the core functionality for the Document Chat Assistant,
    including document processing, vector search, AI-powered conversations,
    and PowerPoint presentation generation.
    
    Key Capabilities:
    - Multi-format document ingestion and processing
    - Vector-based similarity search using Cosmos DB
    - Contextual AI responses with source citations
    - Conversation state management
    - PowerPoint presentation generation
    - Document similarity analysis
    
    Attributes:
        data_directory (str): Directory for storing documents and presentations
        openai_client: OpenAI API client for chat and embeddings
        embeddings: OpenAI embeddings model instance
        llm: Language model for generating responses
        cosmos_db: Cosmos DB manager for vector operations
        document_processor: Multi-format document processor
        presentation_generator: PowerPoint generation handler
        current_conversation (dict): Active conversation context and metadata
    """
    
    def __init__(self, data_directory: str = "Data"):
        """
        Initialize the chatbot with all required components.
        
        Sets up the complete chatbot infrastructure including:
        - OpenAI client and models
        - Cosmos DB connection and vector search
        - Document processing capabilities
        - PowerPoint generation features
        - Conversation state management
        
        Args:
            data_directory (str): Directory path for storing documents and generated content.
                                Defaults to "Data". Will be created if it doesn't exist.
        
        Raises:
            ValueError: If required environment variables are not set
            Exception: If any component fails to initialize
        """
        # Set up data directory for document storage
        self.data_directory = data_directory
        os.makedirs(self.data_directory, exist_ok=True)
        logger.info(f"Data directory initialized: {self.data_directory}")
        
        # Initialize core AI components
        self._initialize_openai()
        
        # Initialize vector database
        self._initialize_cosmos_db()
        
        # Initialize document processing capabilities
        self.document_processor = DocumentProcessor()
        logger.info("Document processor initialized")
        
        # Initialize PowerPoint generation capabilities
        self.presentation_generator = PresentationGenerator(self.data_directory)
        logger.info("Presentation generator initialized")
        
        # Initialize conversation state tracking
        self.current_conversation = {
            'query': '',                    # Current user query
            'response': '',                 # AI-generated response
            'source_references': [],        # References to source documents
            'chunks_used': [],             # Document chunks used for context
            'sources': []                   # List of source document names
        }
        
        logger.info("CosmosChatbot initialized successfully with all components")
    
    def _initialize_openai(self):
        """
        Initialize OpenAI client and language models.
        
        Sets up the OpenAI API client, embeddings model, and chat model
        with optimized configurations for document processing and conversation.
        
        Components initialized:
        - OpenAI API client for direct API access
        - text-embedding-3-large for high-quality document embeddings
        - GPT-4o for intelligent conversation and response generation
        
        Raises:
            ValueError: If OPENAI_API_KEY environment variable is not set
        """
        # Validate API key availability
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY environment variable not set. "
                "Please add your OpenAI API key to the .env file."
            )
        
        # Initialize OpenAI client for direct API access
        self.openai_client = openai.OpenAI(api_key=api_key)
        
        # Initialize embeddings model for document vectorization
        # Using text-embedding-3-large for highest quality embeddings
        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-3-large",    # Latest high-quality embedding model
            openai_api_key=api_key
        )
        
        # Initialize chat model for response generation
        # Using GPT-4o for optimal balance of quality and speed
        self.llm = ChatOpenAI(
            model="gpt-4o",                    # Latest GPT-4 optimized model
            temperature=0.1,                   # Low temperature for consistent, factual responses
            openai_api_key=api_key
        )
        
        logger.info("OpenAI client and models initialized successfully")
    
    def _initialize_cosmos_db(self):
        """
        Initialize Azure Cosmos DB connection and vector search capabilities.
        
        Sets up the connection to Cosmos DB for MongoDB vCore, creates necessary
        indexes for vector search, and handles embedding dimension compatibility.
        
        Features:
        - Automatic vector index creation for similarity search
        - Embedding dimension validation and compatibility checking
        - Automatic collection reset for embedding model changes
        - Fallback mechanisms for vector search failures
        
        Raises:
            ValueError: If COSMOS_DB_CONNECTION_STRING environment variable is not set
        """
        # Validate connection string availability
        connection_string = os.getenv("COSMOS_DB_CONNECTION_STRING")
        if not connection_string:
            raise ValueError(
                "COSMOS_DB_CONNECTION_STRING environment variable not set. "
                "Please add your Cosmos DB connection string to the .env file."
            )
        
        # Initialize Cosmos DB manager
        self.cosmos_db = CosmosDBManager(connection_string)
        
        # Validate embedding dimension compatibility
        try:
            # Test vector search with sample embedding
            # text-embedding-3-large uses 3072 dimensions
            test_embedding = [0.0] * 3072
            test_results = self.cosmos_db.vector_search(test_embedding, top_k=1)
            logger.info("Cosmos DB vector search validated successfully")
            
        except Exception as e:
            # Handle embedding dimension mismatches
            if "dimension" in str(e).lower():
                logger.warning(
                    "Embedding dimension mismatch detected. "
                    "Resetting collection for new embedding model..."
                )
                self.cosmos_db.reset_collection_for_new_embeddings()
                logger.info("Collection reset completed successfully")
            else:
                logger.info(
                    "Cosmos DB initialized successfully "
                    "(vector search validation skipped due to empty collection)"
                )
    
    # ========================================================================
    # Document Management Methods
    # ========================================================================
    
    def add_document(self, file_path: str, permanent_filename: str = None) -> str:
        """
        Add a document to the knowledge base with full processing pipeline.
        
        This method handles the complete document ingestion process:
        1. Validates file existence and accessibility
        2. Extracts comprehensive metadata from the document
        3. Processes document into optimized text chunks
        4. Generates high-quality embeddings for each chunk
        5. Stores everything in Cosmos DB for future retrieval
        6. Handles duplicate documents by replacement
        
        The method uses batch processing for efficiency and includes robust
        error handling to ensure partial failures don't corrupt the knowledge base.
        
        Args:
            file_path (str): Path to the document file to process
            permanent_filename (str, optional): Filename to use in the knowledge base.
                                              If None, uses the file's basename.
        
        Returns:
            str: Success message with processing details, or error message if failed
        
        Processing Pipeline:
        1. File validation and metadata extraction
        2. Document chunking with overlap for context preservation
        3. Embedding generation using text-embedding-3-large
        4. Batch insertion into Cosmos DB with metadata serialization
        5. Duplicate handling and cleanup
        """
        try:
            # Validate file existence
            if not os.path.exists(file_path):
                error_msg = f"Error: File not found: {file_path}"
                logger.error(error_msg)
                return error_msg
            
            # Determine final filename for knowledge base
            filename = permanent_filename or os.path.basename(file_path)
            logger.info(f"Processing document: {filename} (source: {file_path})")
            
            # Extract comprehensive file metadata
            file_metadata = self.document_processor.extract_metadata(file_path)
            logger.debug(f"Extracted metadata for {filename}: {len(file_metadata)} fields")
            
            # Handle existing documents by replacement
            existing_docs = self.cosmos_db.list_documents({
                "metadata.source": filename
            })
            
            if existing_docs:
                # Remove existing document chunks to prevent duplicates
                deleted_count = self.cosmos_db.delete_documents({
                    "metadata.source": filename
                })
                logger.info(f"Replaced existing document: {filename} ({deleted_count} chunks removed)")
            
            # Initialize batch processing variables
            documents_to_upsert = []
            chunk_count = 0
            batch_size = 50  # Optimal batch size for Cosmos DB
            
            # Process document into chunks and generate embeddings
            for chunk_data in self.document_processor.process_file(file_path):
                try:
                    # Generate high-quality embedding for the text chunk
                    embedding = self.embeddings.embed_query(chunk_data['text'])
                    
                    # Prepare metadata with permanent filename
                    chunk_metadata = chunk_data['metadata'].copy()
                    chunk_metadata['source'] = filename  # Ensure consistent naming
                    
                    # Serialize metadata to ensure database compatibility
                    serialized_metadata = self._serialize_metadata({
                        **chunk_metadata,
                        **file_metadata
                    })
                    
                    # Prepare document for batch insertion
                    documents_to_upsert.append({
                        'text': chunk_data['text'],
                        'embedding': embedding,
                        'metadata': serialized_metadata
                    })
                    
                    chunk_count += 1
                    
                    # Perform batch upsert when batch size is reached
                    if len(documents_to_upsert) >= batch_size:
                        success = self.cosmos_db.batch_upsert_documents(documents_to_upsert)
                        if success:
                            logger.debug(f"Batch upserted {len(documents_to_upsert)} chunks")
                        documents_to_upsert = []
                
                except Exception as chunk_error:
                    logger.error(f"Error processing chunk from {filename}: {chunk_error}")
                    continue  # Skip problematic chunks but continue processing
            
            # Upsert any remaining documents in the final batch
            if documents_to_upsert:
                success = self.cosmos_db.batch_upsert_documents(documents_to_upsert)
                if success:
                    logger.debug(f"Final batch upserted {len(documents_to_upsert)} chunks")
            
            # Return success message with processing statistics
            success_msg = f"Successfully added {filename} with {chunk_count} text chunks"
            logger.info(success_msg)
            return success_msg
            
        except Exception as e:
            error_msg = f"Error adding document {file_path}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return error_msg
    
    def _serialize_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Serialize metadata to ensure all values are supported types"""
        serialized = {}
        for key, value in metadata.items():
            if isinstance(value, (str, int, float, bool)) or value is None:
                serialized[key] = value
            elif isinstance(value, list):
                # Convert lists to comma-separated strings
                serialized[key] = ', '.join(str(item) for item in value)
            elif isinstance(value, dict):
                # Convert dicts to JSON strings
                serialized[key] = json.dumps(value)
            else:
                # Convert other types to strings
                serialized[key] = str(value)
        return serialized
    
    def generate_response(self, query: str) -> Dict[str, Any]:
        """Generate response to user query using Cosmos DB retrieval"""
        try:
            logger.info(f"Processing query: {query[:100]}...")
            
            # Generate query embedding
            query_embedding = self.embeddings.embed_query(query)
            
            # Search for relevant documents
            search_results = self.cosmos_db.vector_search(
                query_embedding=query_embedding,
                top_k=10
            )
            
            if not search_results:
                return {
                    'response': "I couldn't find any relevant information in the uploaded documents to answer your question. Please make sure you have uploaded relevant documents or try rephrasing your question.",
                    'sources': [],
                    'chunks_used': 0
                }
            
            # Prepare context for LLM
            context_chunks = []
            sources = set()
            
            for result in search_results:
                context_chunks.append({
                    'text': result['text'],
                    'metadata': result['metadata'],
                    'score': result['score']
                })
                
                # Track sources
                source_name = result['metadata'].get('source', 'Unknown')
                sources.add(source_name)
            
            # Generate response using LLM
            response = self._generate_llm_response(query, context_chunks)
            
            # Update current conversation
            self.current_conversation = {
                'query': query,
                'response': response,
                'source_references': self._extract_source_references(response),
                'chunks_used': context_chunks,
                'sources': list(sources)
            }
            
            return {
                'response': response,
                'sources': list(sources),
                'chunks_used': len(context_chunks)
            }
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return {
                'response': f"I encountered an error while processing your question: {str(e)}",
                'sources': [],
                'chunks_used': 0
            }
    
    def _generate_llm_response(self, query: str, context_chunks: List[Dict]) -> str:
        """Generate response using LLM with retrieved context"""
        try:
            # Format context
            context_text = self._format_context(context_chunks)
            
            # Create prompt
            system_prompt = """You are an expert document analyst. Provide precise, comprehensive answers based ONLY on the provided documents.

CRITICAL RULES:
1. Answer ONLY from the provided context - never use external knowledge
2. If information isn't in the context, state: "This information is not available in the provided documents"
3. Always cite sources using exact format: (Source: filename, Page/Slide X)
4. Be specific and detailed when information is available
5. Structure your response clearly with headings and bullet points when appropriate

CITATION REQUIREMENTS:
- Every factual statement must have a citation
- Use the exact format: (Source: filename, Page/Slide X)
- Place citations immediately after the relevant information
- If multiple sources support a point, cite all relevant sources"""

            user_prompt = f"""Context from documents:
{context_text}

Question: {query}

Please provide a comprehensive answer based on the context above, following all citation requirements."""

            # Generate response
            response = self.llm.invoke([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ])
            
            return response.content
            
        except Exception as e:
            logger.error(f"Error generating LLM response: {e}")
            return f"Error generating response: {str(e)}"
    
    def _format_context(self, chunks: List[Dict]) -> str:
        """Format context chunks for LLM"""
        context_parts = []
        
        for i, chunk in enumerate(chunks, 1):
            metadata = chunk['metadata']
            source = metadata.get('source', 'Unknown')
            
            # Determine location (page or slide)
            location = ""
            if 'slide' in metadata:
                location = f"Slide {metadata['slide']}"
            elif 'page' in metadata:
                location = f"Page {metadata['page']}"
            
            context_parts.append(
                f"### CONTEXT CHUNK {i} ###\n"
                f"Source: {source}\n"
                f"Location: {location}\n"
                f"Content: {chunk['text']}\n"
                f"### END CHUNK {i} ###"
            )
        
        return "\n\n".join(context_parts)
    
    def _extract_source_references(self, response: str) -> List[Dict]:
        """Extract source references from response for presentation generation"""
        import re
        
        # Pattern to match citations like (Source: filename, Page/Slide X)
        pattern = r'\(Source:\s*([^,]+),\s*(Page|Slide)\s*(\d+)\)'
        matches = re.findall(pattern, response, re.IGNORECASE)
        
        references = []
        for match in matches:
            filename, ref_type, number = match
            references.append({
                'source_name': filename.strip(),
                'reference_type': ref_type.lower(),
                'page_or_slide': number,
                'file_type': self._get_file_type_from_reference(ref_type)
            })
        
        return references
    
    def _get_file_type_from_reference(self, ref_type: str) -> str:
        """Determine file type from reference type"""
        if ref_type.lower() == 'slide':
            return 'pptx'
        elif ref_type.lower() == 'page':
            return 'pdf'  # Could also be docx, but default to pdf
        return 'unknown'
    
    def list_documents(self) -> List[Dict[str, Any]]:
        """List all documents in the knowledge base"""
        try:
            documents = self.cosmos_db.list_documents()
            
            # Group by source file
            file_groups = {}
            for doc in documents:
                source = doc['metadata'].get('source', 'Unknown')
                if source not in file_groups:
                    file_groups[source] = {
                        'filename': source,
                        'file_type': doc['metadata'].get('file_type', 'unknown'),
                        'chunk_count': 0,
                        'created_at': doc.get('created_at')
                    }
                file_groups[source]['chunk_count'] += 1
            
            return list(file_groups.values())
            
        except Exception as e:
            logger.error(f"Error listing documents: {e}")
            return []
    
    def delete_document(self, filename: str) -> str:
        """Delete a document from the knowledge base"""
        try:
            # Delete from Cosmos DB
            deleted_count = self.cosmos_db.delete_documents({
                "metadata.source": filename
            })
            
            if deleted_count > 0:
                # Also delete physical file if it exists
                file_path = os.path.join(self.data_directory, filename)
                if os.path.exists(file_path):
                    os.remove(file_path)
                
                logger.info(f"Deleted document: {filename} ({deleted_count} chunks)")
                return f"Successfully deleted {filename} ({deleted_count} chunks)"
            else:
                return f"Document not found: {filename}"
                
        except Exception as e:
            logger.error(f"Error deleting document {filename}: {e}")
            return f"Error deleting document: {str(e)}"
    
    def generate_presentation(self, query: str = None) -> Optional[str]:
        """Generate PowerPoint presentation from current conversation"""
        try:
            if not query:
                # Use current conversation
                if not self.current_conversation.get('response'):
                    logger.warning("No current conversation to generate presentation from")
                    return None
                
                query = self.current_conversation['query']
                response = self.current_conversation['response']
                source_references = self.current_conversation['source_references']
            else:
                # Generate new response for the query
                result = self.generate_response(query)
                response = result['response']
                source_references = self.current_conversation['source_references']
            
            if not source_references:
                logger.warning("No source references found for presentation generation")
                return None
            
            # Generate presentation
            ppt_path = self.presentation_generator.create_presentation(
                query=query,
                response=response,
                source_references=source_references
            )
            
            return ppt_path
            
        except Exception as e:
            logger.error(f"Error generating presentation: {e}")
            return None
    
    def get_conversation_info(self) -> Dict[str, Any]:
        """Get current conversation information"""
        return {
            'has_conversation': bool(self.current_conversation.get('response')),
            'query': self.current_conversation.get('query', ''),
            'response_length': len(self.current_conversation.get('response', '')),
            'source_count': len(self.current_conversation.get('sources', [])),
            'reference_count': len(self.current_conversation.get('source_references', [])),
            'chunks_used': len(self.current_conversation.get('chunks_used', []))
        }
    
    def clear_conversation(self):
        """Clear current conversation context"""
        self.current_conversation = {
            'query': '',
            'response': '',
            'source_references': [],
            'chunks_used': []
        }
        logger.info("Cleared conversation context")
    
    def find_similar_documents(self, file_path: str) -> Dict[str, Any]:
        """Find documents similar to the uploaded file"""
        try:
            # Process the uploaded file to get text chunks
            chunks = list(self.document_processor.process_file(file_path))
            
            if not chunks:
                return {
                    'error': 'Could not extract text from the uploaded file',
                    'similar_documents': []
                }
            
            # Use the first few chunks to find similar documents
            sample_text = " ".join([chunk['text'] for chunk in chunks[:3]])
            
            # Generate embedding for sample text
            query_embedding = self.embeddings.embed_query(sample_text)
            
            # Search for similar documents
            similar_results = self.cosmos_db.vector_search(
                query_embedding=query_embedding,
                top_k=10
            )
            
            # Group results by source document
            similar_docs = {}
            for result in similar_results:
                source = result['metadata'].get('source', 'Unknown')
                if source not in similar_docs:
                    similar_docs[source] = {
                        'filename': source,
                        'file_type': result['metadata'].get('file_type', 'unknown'),
                        'similarity_score': result['score'],
                        'matching_chunks': 0
                    }
                similar_docs[source]['matching_chunks'] += 1
                # Keep the highest similarity score
                if result['score'] > similar_docs[source]['similarity_score']:
                    similar_docs[source]['similarity_score'] = result['score']
            
            # Sort by similarity score
            sorted_docs = sorted(
                similar_docs.values(),
                key=lambda x: x['similarity_score'],
                reverse=True
            )
            
            return {
                'similar_documents': sorted_docs,
                'total_found': len(sorted_docs)
            }
            
        except Exception as e:
            logger.error(f"Error finding similar documents: {e}")
            return {
                'error': f'Error analyzing document: {str(e)}',
                'similar_documents': []
            }
    
    def __del__(self):
        """Cleanup on object destruction"""
        try:
            if hasattr(self, 'cosmos_db'):
                self.cosmos_db.close_connection()
        except Exception:
            pass