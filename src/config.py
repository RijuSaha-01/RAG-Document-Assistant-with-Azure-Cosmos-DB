
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Central configuration management"""
    
    # API Keys & Credentials
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    COSMOS_DB_CONNECTION_STRING = os.getenv("COSMOS_DB_CONNECTION_STRING")
    
    # Cosmos DB Settings
    DB_NAME = "document_chatbot"
    COLLECTION_NAME = "documents"
    EMBEDDING_DIMENSION = 3072  # for text-embedding-3-large
    
    # Model Settings
    EMBEDDING_MODEL = "text-embedding-3-large"
    CHAT_MODEL = "gpt-4o"
    
    # Paths
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DATA_DIR = os.path.join(BASE_DIR, "data")
    
    @classmethod
    def validate(cls):
        """Validate critical configuration"""
        missing = []
        if not cls.OPENAI_API_KEY:
            missing.append("OPENAI_API_KEY")
        if not cls.COSMOS_DB_CONNECTION_STRING:
            missing.append("COSMOS_DB_CONNECTION_STRING")
            
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

# Create data directory if it doesn't exist
os.makedirs(Config.DATA_DIR, exist_ok=True)
