
# RAG Document Assistant with Azure Cosmos DB

An intelligent document assistant that uses Retrieval-Augmented Generation (RAG) to chat with your documents (PDF, DOCX, PPTX) and generate PowerPoint summaries. built with Python, Azure Cosmos DB for MongoDB vCore (Vector Search), and OpenAI GPT-4o.

## 🚀 Features

*   **Multi-Format Support**: Ingest PDF, Word, and PowerPoint documents.
*   **Vector Search**: Uses Azure Cosmos DB as a high-performance vector store.
*   **Smart Retrieval**: Semantically searches documents to find relevant context.
*   **Presentation Generation**: Automatically creates PPT summaries of the answer (Windows COM integration optional but supported).
*   **Clean Architecture**: Modular design separating ingestion, retrieval, and generation logic.

## 🛠️ Tech Stack

*   **Language**: Python 3.10+
*   **Database**: Azure Cosmos DB for MongoDB vCore
*   **AI/LLM**: OpenAI GPT-4o, text-embedding-3-large
*   **Framework**: Flask (API)
*   **Tools**: LangChain, PyMuPDF, python-pptx

## 📦 Project Structure

```
rag-document-assistant/
├── src/
│   ├── app.py              # API functionality
│   ├── rag_pipeline.py     # Core RAG logic
│   ├── document_loader.py  # File processing
│   ├── vector_store.py     # Database interactions
│   ├── presentation.py     # PPTX generation
│   └── config.py           # Settings
├── tests/                  # Basic verification tests
├── data/                   # Document storage
└── requirements.txt        # Dependencies
```

## 🏃‍♂️ Quick Start

1.  **Clone the repository**
    ```bash
    git clone https://github.com/yourusername/rag-document-assistant.git
    cd rag-document-assistant
    ```

2.  **Set up Environment**
    ```bash
    # Create virtual env
    python -m venv .venv
    
    # Activate (Windows)
    .venv\Scripts\activate
    
    # Install dependencies
    pip install -r requirements.txt
    ```

3.  **Configure Credentials**
    Copy `.env.example` to `.env` and fill in your keys:
    ```bash
    OPENAI_API_KEY=sk-...
    COSMOS_DB_CONNECTION_STRING=mongodb+srv://...
    ```

4.  **Run the Server**
    ```bash
    python -m src.app
    ```

## 📝 Learning Outcomes

This project demonstrates:
*   Implementation of a production-like RAG pipeline.
*   Handling diverse unstructured data formats.
*   Integration with cloud-native vector databases.
*   Writing clean, modular, and maintainable Python code.

## ⚠️ Limitations

*   **Presentation Generation**: The high-fidelity "Slide Copy" feature uses Windows COM and requires PowerPoint to be installed on the host machine. A basic fallback exists for other OSs.
*   **Database**: Meant to run with Azure Cosmos DB vCore; easy to adapt for local Chroma/FAISS.
