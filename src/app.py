
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
import os
from src.rag_pipeline import RAGPipeline
from src.config import Config
from src.utils import setup_logging

app = Flask(__name__)
logger = setup_logging(__name__)

# Initialize Pipeline
pipeline = None

def get_pipeline():
    global pipeline
    if pipeline is None:
        try:
            pipeline = RAGPipeline()
            logger.info("RAG Pipeline Initialized")
        except Exception as e:
            logger.error(f"Failed to init pipeline: {e}")
            return None
    return pipeline

@app.route('/api/chat', methods=['POST'])
def chat():
    rag = get_pipeline()
    if not rag: return jsonify({"error": "System not ready"}), 500
    
    data = request.json
    query = data.get('message')
    if not query: return jsonify({"error": "No message"}), 400
    
    result = rag.query(query)
    return jsonify(result)

@app.route('/api/upload', methods=['POST'])
def upload():
    rag = get_pipeline()
    if not rag: return jsonify({"error": "System not ready"}), 500
    
    if 'file' not in request.files:
        return jsonify({"error": "No file"}), 400
        
    file = request.files['file']
    if not file.filename:
        return jsonify({"error": "No filename"}), 400
        
    filename = secure_filename(file.filename)
    save_path = os.path.join(Config.DATA_DIR, filename)
    file.save(save_path)
    
    msg = rag.ingest_document(save_path)
    return jsonify({"message": msg})

@app.route('/health')
def health():
    return jsonify({"status": "ok", "pipeline_ready": pipeline is not None})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
