
# RAG Document Assistant with Azure Cosmos DB

A **portfolio / learning project** that demonstrates a **Retrieval-Augmented Generation (RAG)** pipeline using **Azure Cosmos DB (MongoDB API)** and **OpenAI models**.

This project is designed for **educational purposes** and to showcase understanding of modern AI application patterns — it is **not production software**.

---

## 🚀 What This Project Does

- Ingests documents (PDF, TXT, DOCX)
- Splits text into chunks
- Generates embeddings using OpenAI
- Stores embeddings in Azure Cosmos DB (vector search)
- Retrieves relevant chunks for a user query
- Generates an AI-assisted answer using retrieved context

---

## 🧠 How RAG Works (Simplified)

```

User Question
↓
Vector Search (Cosmos DB)
↓
Relevant Document Chunks
↓
Prompt + Context
↓
LLM Answer

```

---

## 🛠 Tech Stack

- Python
- OpenAI API
- Azure Cosmos DB (MongoDB API + vector search)
- Flask
- PyPDF / python-docx

---

## 📂 Project Structure

```

.
├── src/
│   ├── app.py
│   ├── rag_pipeline.py
│   ├── document_processor.py
│   ├── vector_store.py
│   ├── presentation.py
│   └── config.py
├── tests/
│   └── test_basic_flow.py
├── .env.example
├── .gitignore
└── README.md

```

---

## ⚙️ Setup Instructions

### 1️⃣ Clone the repository
```bash
git clone https://github.com/RijuSaha-01/RAG-Document-Assistant-with-Azure-Cosmos-DB
cd RAG-Document-Assistant-with-Azure-Cosmos-DB
```

### 2️⃣ Create virtual environment

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
```

### 3️⃣ Install dependencies

```bash
pip install -r requirements.txt
```

### 4️⃣ Environment variables

```bash
cp .env.example .env
```

Fill in your own keys inside `.env`.

---

## ▶️ Running the App

```bash
python -m src.app
```

---

## 🧪 Running Tests

```bash
pytest
```

---

## ⚠️ Platform Limitations

* `presentation.py` uses **Windows COM automation**
* PowerPoint generation works **only on Windows**
* This feature is optional and not required for core RAG functionality

---

## 🔐 Security Notes

* No secrets are committed to this repository
* `.env` files must remain local
* Always rotate keys if you accidentally commit them

---

## 📌 Limitations

* No authentication
* Minimal error handling
* Designed for small-scale experimentation
* No production deployment setup

---

## 🔮 Future Improvements

* Better chunking strategies
* Metadata-based retrieval
* UI frontend
* Cross-platform document export

---

## 📄 License

MIT License
