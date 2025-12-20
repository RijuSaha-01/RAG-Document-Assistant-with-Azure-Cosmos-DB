# Architecture & Design Notes

This document outlines the high-level architecture, key design decisions, and potential future improvements for the **RAG Document Assistant**. This project serves as a portfolio piece to demonstrate my skills in building production-ready RAG systems using modern cloud technologies.

## 🏗️ High-Level Architecture

The architecture is built around a **Flask REST API** that serves as the backend, powering a simple HTML/JS web interface. The core components are:

-   **API Backend (Flask)**: The main entry point for all user interactions. It handles chat requests, document uploads, and other operations.
-   **Document Processor**: A Python module responsible for extracting text and metadata from various document formats (PDF, DOCX, PPTX).
-   **Cosmos DB Manager (Azure Cosmos DB for MongoDB vCore)**: Manages all interactions with the database. It is responsible for storing text vectors and document metadata, as well as performing efficient vector similarity searches.
-   **Chatbot Logic (OpenAI Models)**: The core RAG logic resides here. It enriches user queries using OpenAI models, retrieves relevant documents from Cosmos DB, and generates a contextualized, cited response.
-   **Presentation Generator (Optional, COM-based)**: A unique feature that automatically generates PowerPoint presentations based on the conversation history, showcasing the system's content generation capabilities.

### Data Flow Diagram

```
User -> Web UI (index.html) -> Flask API
    |
    +-> (Upload) -> Document Processor -> Embeddings -> Cosmos DB Manager
    |
    +-> (Chat) -> Chatbot Logic -> [Retrieval] -> Cosmos DB Manager
                     |
                     +-> [Generation] -> OpenAI LLM -> Response to Web UI
```

## ⚖️ Key Design Decisions & Trade-offs

The project's design prioritized a balance between performance, scalability, and development simplicity.

1.  **Database Choice: Azure Cosmos DB for MongoDB vCore**
    *   **Why**: I chose Cosmos DB for its native vector search capabilities, managed scalability, and seamless integration with the Azure ecosystem. It eliminates the need to manage a separate vector database.
    *   **Trade-off**: While powerful, it can be more costly for smaller projects than self-hosted alternatives. For a production-ready application, however, the scalability and maintenance benefits are worth it.

2.  **Backend Structure: Monolithic REST API with Flask**
    *   **Why**: For this project, a monolithic REST API provides simplicity and rapid development. I structured the code into distinct modules (document processor, DB manager, chat logic) with clear separation of concerns to ensure maintainability.
    *   **Trade-off**: For a very large-scale application, a microservices architecture might offer more flexibility but would introduce significant complexity. The current approach is ideal for most use cases.

3.  **Document Processing: Synchronous Processing**
    *   **Why**: Documents are processed synchronously upon upload to make them immediately available for querying. This design provides a straightforward user experience.
    *   **Trade-off**: For very large documents or bulk uploads, this approach can block the API. A future improvement would be to implement an asynchronous task queue (like Celery) to process documents in the background.

4.  **Presentation Generation: Windows COM Integration**
    *   **Why**: I implemented this feature to demonstrate integration with external systems and to automate the generation of structured content beyond simple chat. It leverages COM automation to build PPTX slides.
    *   **Trade-off**: This feature is inherently platform-dependent (Windows-only) and requires PowerPoint to be installed. It was a conscious trade-off to showcase a unique capability at the cost of universal portability. The component is designed to be optional.

## 🚀 Future Improvement Opportunities

To demonstrate forward-thinking, I have identified several areas for future enhancements:

-   **Asynchronous Document Processing**: Implement a task queue system (e.g., Celery with Redis) to handle document uploads asynchronously. This would greatly improve API responsiveness and scalability under heavy load.
-   **Comprehensive Test Suite**: Build out a robust test suite using `pytest` to cover unit tests for each module and integration tests for the API flows. This would ensure long-term reliability and maintainability.
-   **Containerization**: Create `Dockerfile` and `docker-compose.yml` files to containerize the application. This would simplify the development setup and standardize production deployment on any cloud platform.
-   **API Rate Limiting & Enhanced Security**: Integrate a library to enforce rate limiting against API abuse and explore more advanced security measures like token-based authentication (e.g., JWT) for multi-user applications.
-   **Microservices Architecture**: For extreme scale, the current monolith could be broken down into microservices (e.g., a service for document processing, one for chat, etc.) that can be deployed and scaled independently.
-   **Multi-language Support**: Extend the document processor and RAG pipeline to effectively handle and search documents in languages other than English.

These notes should provide a clear understanding of the project's architecture, the rationale behind key decisions, and the potential path for future development.
