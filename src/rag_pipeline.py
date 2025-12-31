
from typing import List, Dict, Any
import logging
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from src.config import Config
from src.vector_store import VectorStore
from src.document_processor import DocumentProcessor
from src.presentation import PresentationGenerator
from src.utils import setup_logging

# Setup logging
logger = setup_logging(__name__)

class RAGPipeline:
    """
    RAG (Retrieval-Augmented Generation) Pipeline
    Connects Document Processing -> Vector Storage -> Semantic Search -> LLM Generation
    """
    
    def __init__(self):
        # Validate configuration (API keys, connection strings)
        Config.validate()
        
        # Initialize core components
        self.vector_store = VectorStore()
        self.doc_processor = DocumentProcessor()
        self.presentation_gen = PresentationGenerator(Config.DATA_DIR)
        
        # Initialize OpenAI Models
        # text-embedding-3-large is used for high-dimensional semantic vectors
        self.embeddings = OpenAIEmbeddings(
            model=Config.EMBEDDING_MODEL,
            openai_api_key=Config.OPENAI_API_KEY
        )
        # GPT-4o is used for intelligent answer synthesis
        self.llm = ChatOpenAI(
            model=Config.CHAT_MODEL,
            openai_api_key=Config.OPENAI_API_KEY,
            temperature=0.3
        )

    def ingest_document(self, file_path: str):
        """
        Ingest a document into the system:
        1. Parse file and split into text chunks
        2. Generate vector embeddings for each chunk
        3. Store vectors and metadata in Cosmos DB
        """
        logger.info(f"Ingesting: {file_path}")
        
        # Step 1: Document Loading & Chunking
        # We break the text into smaller pieces to ensure we can retrieve specific context effectively.
        chunks = self.doc_processor.process_file(file_path)
        
        if not chunks:
            return "No content extracted."
            
        # Step 2: Embedding Generation
        # Convert text chunks into mathematical vectors that represent semantic meaning.
        texts = [chunk['text'] for chunk in chunks]
        vectors = self.embeddings.embed_documents(texts)
        
        for i, chunk in enumerate(chunks):
            chunk['embedding'] = vectors[i]
            
        # Step 3: Vector Storage
        # Store the embeddings in Cosmos DB so we can perform fast similarity searches later.
        count = self.vector_store.add_documents(chunks)
        return f"Successfully processed {count} chunks from document."

    def query(self, user_query: str) -> Dict[str, Any]:
        """
        Process a user query using the RAG flow:
        1. Embed the user query
        2. Retrieve semantically similar chunks from the database
        3. Use retrieved context to generate a factual response via LLM
        """
        # Step 1: Embed Query
        # We must use the same embedding model used for the documents to ensure compatibility.
        query_vector = self.embeddings.embed_query(user_query)
        
        # Step 2: Semantic Retrieval
        # Find the top-K most relevant document chunks based on vector distance.
        results = self.vector_store.search(query_vector)
        
        # Step 3: Context Construction
        # Combine the retrieved text into a single context block for the LLM.
        context_parts = []
        for r in results:
            source = r['metadata'].get('source', 'Unknown')
            context_parts.append(f"Source ({source}): {r['text']}")
        
        context_text = "\n\n".join(context_parts)
        
        if not context_text:
            return {"response": "I couldn't find any relevant information in your documents."}
            
        # Step 4: Answer Generation
        # Prompt the LLM to answer the question ONLY using the provided context.
        system_prompt = (
            "You are a helpful assistant. Provide an answer based ONLY on the provided context. "
            "Always cite the source document name. If the information is not in the context, "
            "clearly state that the information is not available in the documents."
        )
        user_prompt = f"Context:\n{context_text}\n\nQuestion: {user_query}"
        
        response = self.llm.invoke([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ])
        
        return {
            "response": response.content,
            "sources": list(set([r['metadata']['source'] for r in results]))
        }

    def create_presentation(self, query: str, summary: str):
        """Invoke the presentation generator for the current conversation"""
        return self.presentation_gen.generate(
            title=f"Response to: {query}", 
            summary=summary, 
            references=[] 
        )
