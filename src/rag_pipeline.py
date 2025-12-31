
from typing import List, Dict, Any
import logging
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from src.config import Config
from src.vector_store import VectorStore
from src.document_loader import DocumentLoader
from src.presentation import PresentationGenerator
from src.utils import setup_logging

logger = setup_logging(__name__)

class RAGPipeline:
    """
    RAG Pipeline that connects:
    DocumentLoader -> OpenAI Embeddings -> VectorStore -> Retrieval -> GPT-4o
    """
    
    def __init__(self):
        Config.validate()
        
        self.vector_store = VectorStore()
        self.doc_loader = DocumentLoader()
        self.presentation_gen = PresentationGenerator(Config.DATA_DIR)
        
        # Initialize OpenAI Models
        self.embeddings = OpenAIEmbeddings(
            model=Config.EMBEDDING_MODEL,
            openai_api_key=Config.OPENAI_API_KEY
        )
        self.llm = ChatOpenAI(
            model=Config.CHAT_MODEL,
            openai_api_key=Config.OPENAI_API_KEY,
            temperature=0.3
        )

    def ingest_document(self, file_path: str):
        """Process and index a document"""
        logger.info(f"Ingesting: {file_path}")
        chunks = self.doc_loader.process_file(file_path)
        
        if not chunks:
            return "No content extracted."
            
        # Generate Embeddings
        # Note: In a production app, we would batch this.
        texts = [chunk['text'] for chunk in chunks]
        vectors = self.embeddings.embed_documents(texts)
        
        for i, chunk in enumerate(chunks):
            chunk['embedding'] = vectors[i]
            
        # Store
        count = self.vector_store.add_documents(chunks)
        return f"Successfully processed {count} chunks from document."

    def query(self, user_query: str) -> Dict[str, Any]:
        """Run the RAG flow"""
        # 1. Embed Query
        query_vector = self.embeddings.embed_query(user_query)
        
        # 2. Retrieve Documents
        results = self.vector_store.search(query_vector)
        
        # 3. Construct Context
        context_text = "\n\n".join(
            [f"Source ({r['metadata']['source']}): {r['text']}" for r in results]
        )
        
        if not context_text:
            return {"response": "No relevant info found in documents."}
            
        # 4. Generate Answer
        system_prompt = (
            "You are a helpful assistant. Use the provided context to answer the user's question. "
            "Cite your sources. If the answer isn't in the context, say so."
        )
        user_prompt = f"Context:\n{context_text}\n\nQuestion: {user_query}"
        
        response = self.llm.invoke([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ])
        
        return {
            "response": response.content,
            "sources": [r['metadata']['source'] for r in results]
        }

    def create_presentation(self, query: str, summary: str):
        """Generate a presentation based on query results"""
        return self.presentation_gen.generate(
            title=f"Response to: {query}", 
            summary=summary, 
            references=[] # Simplified for now
        )
