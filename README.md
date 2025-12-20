# 🤖 RAG Document Assistant with Azure Cosmos DB

This project, built and maintained by **<YOUR NAME>**, is a sophisticated AI-powered document chatbot. I designed, refactored, and documented this application to serve as a portfolio piece showcasing my skills in RAG systems, backend engineering, and cloud architecture. It processes PDFs, PowerPoint presentations, and Word documents, using Azure Cosmos DB for MongoDB vCore for scalable vector similarity search, and enables intelligent conversations with documents through advanced AI capabilities.

## 👤 About the Developer

I am a software engineer based in **<YOUR CITY, COUNTRY>** with a strong focus on building intelligent, scalable, and production-ready applications. My primary areas of expertise include Retrieval-Augmented Generation (RAG) systems, cloud computing (especially Azure), and backend engineering for LLM-powered applications.

- **GitHub**: [<YOUR GITHUB URL>](<YOUR GITHUB URL>)
- **LinkedIn**: [<YOUR LINKEDIN URL>](<YOUR LINKEDIN URL>)
- **Portfolio**: [<YOUR PORTFOLIO URL OR “N/A”>](<YOUR PORTFOLIO URL OR “N/A”>)

## 🛠️ What I Implemented / Refactored

As the sole developer for this version, I was responsible for the architecture, implementation, and documentation. Here are the key contributions I made:

- **Refactored the Backend**: I architected and refactored the Python backend into a production-ready and modular structure. This includes a Flask REST API, a dedicated `CosmosDBManager` for database operations, a `DocumentProcessor` for handling uploads, and a `PresentationGenerator` for automated PowerPoint creation.
- **Enhanced Frontend Functionality (v3.0)**: I implemented and enhanced the frontend-driven features, including LLM query expansion, smart reranking of search results, metadata enrichment for better filtering, document similarity analysis, and the unique auto-PPT generation capability.
- **Wrote and Consolidated Documentation**: I authored the comprehensive documentation, including setup guides, troubleshooting steps, performance notes, and a setup validation script (`setup_validator.py`) to ensure a smooth developer experience.
- **Designed the System Architecture**: I designed the end-to-end data flow, from document ingestion and vectorization to context retrieval and response generation, ensuring a scalable and efficient RAG pipeline.

## ✨ Key Features

- 📄 **Multi-format Document Support**: Process PDF, PPTX, DOCX, PPTM, and DOCM files.
- 🔍 **Advanced Vector Search**: Cosmos DB-powered similarity search with intelligent fallback.
- 🤖 **GPT-4o Integration**: Utilizes advanced language models for intelligent query processing.
- 📊 **Auto-PowerPoint Generation**: Create presentations from conversation context with COM integration.
- 🔄 **Document Similarity Analysis**: Find and analyze related documents in your collection.
- 🌐 **Modern Web Interface**: Clean, responsive UI with real-time chat functionality.
- 🛡️ **Robust Error Handling**: Comprehensive error recovery and logging system.
- 🚀 **Production Ready**: Optimized for performance with batch processing and caching.

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- Azure Cosmos DB for MongoDB vCore account
- OpenAI API key
- Windows OS (for PowerPoint COM integration - this feature is optional)

### Installation & Setup

1. **Clone and Navigate**
   ```bash
   git clone <repository-url>
   cd rag-doc-assistant-<yourname>
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment**
   
   Create a `.env` file in the project root:
   ```env
   # OpenAI Configuration
   OPENAI_API_KEY=your_openai_api_key_here
   
   # Azure Cosmos DB Configuration
   COSMOS_DB_CONNECTION_STRING=mongodb://your-account:your-key@your-account.mongo.cosmos.azure.com:10255/?ssl=true&replicaSet=globaldb&retrywrites=false&maxIdleTimeMS=120000&appName=@your-account@
   ```

4. **Run the Application**
   ```bash
   # Simple run (recommended)
   python run.py
   ```

5. **Access the Application**
   
   Open your browser and navigate to: `http://127.0.0.1:5000`

## 🏗️ Architecture Overview

For a detailed breakdown of the architecture, design decisions, and potential future improvements, please see [ARCHITECTURE_NOTES.md](./ARCHITECTURE_NOTES.md).

### Core Components
```
├── api.py                    # Flask REST API server with all endpoints
├── cosmos_chatbot.py         # Main chatbot logic and conversation management
├── cosmos_db_manager.py      # Cosmos DB operations and vector search
├── document_processor.py     # Multi-format document processing and chunking
├── presentation_generator.py # PowerPoint generation with COM integration
├── run.py                    # Application launcher with validation
├── static/
│   └── index.html           # Modern web interface
├── Data/                    # Document storage and generated presentations
├── .env                     # Environment configuration (create this)
└── requirements.txt         # Python dependencies
```

## 🔧 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Serve web interface |
| `/api/chat` | POST | Process chat messages and return AI responses |
| `/api/add` | POST | Upload and process new documents |
| `/api/list` | GET | List all documents in knowledge base |
| `/api/delete` | POST | Remove documents from knowledge base |
| `/api/analyze` | POST | Analyze document similarity |
| `/api/generate-ppt` | POST | Generate PowerPoint from conversation |
| `/api/download-ppt` | GET | Download generated presentations |
| `/health` | GET | System health and status check |

## 🔍 Troubleshooting

### Common Issues

1. **Installation Problems**: Ensure you are using Python 3.8+ and have installed all packages from `requirements.txt`.
2. **Environment Configuration**: Run `python setup_validator.py` to check if your `.env` file is set up correctly.
3. **Database Connection**: Verify your Cosmos DB connection string and ensure your IP is whitelisted in the Azure portal if network restrictions are in place.
4. **PowerPoint Generation Issues**: This feature requires a Windows OS with PowerPoint installed.

## 📄 License

This project is licensed under the MIT License. See the [LICENSE](./LICENSE) file for details.

This project is for educational and development purposes. Please ensure compliance with OpenAI and Azure terms of service. Others are welcome to clone and modify the project for learning and experimentation, as long as they respect the license and provider terms.

---

**Suggested GitHub topics**: `rag`, `azure-cosmos-db`, `openai`, `flask`, `llm`, `document-chat`, `vector-search`
