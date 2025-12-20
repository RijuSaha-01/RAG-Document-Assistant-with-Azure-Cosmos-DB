"""
Document Chat Assistant API Server
==================================

This module provides the Flask REST API server for the Document Chat Assistant.
It handles all HTTP endpoints for document management, chat functionality, and
PowerPoint presentation generation.

Key Features:
- Document upload and processing
- AI-powered chat with document context
- PowerPoint presentation generation
- Document similarity analysis
- Health monitoring and status checks

Author: Document Chat Assistant Team
Version: 3.0
"""

# Standard library imports
import os
import tempfile
import logging

# Third-party imports
from flask import Flask, request, jsonify, send_from_directory, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

# Local imports
from cosmos_chatbot import CosmosChatbot

# ============================================================================
# Environment Configuration and Validation
# ============================================================================

# Load environment variables from .env file
load_dotenv()

# Verify required API keys are configured
if not os.getenv("OPENAI_API_KEY"):
    raise ValueError(
        "OPENAI_API_KEY environment variable not set. "
        "Please check your .env file and add your OpenAI API key."
    )

if not os.getenv("COSMOS_DB_CONNECTION_STRING"):
    raise ValueError(
        "COSMOS_DB_CONNECTION_STRING environment variable not set. "
        "Please check your .env file and add your Cosmos DB connection string."
    )

# ============================================================================
# Flask Application Setup
# ============================================================================

# Initialize Flask application with static file serving
app = Flask(__name__, static_folder='static', static_url_path='')

# Enable Cross-Origin Resource Sharing for web interface
CORS(app)

# Configure logging for this module
logger = logging.getLogger(__name__)

# ============================================================================
# Chatbot Initialization
# ============================================================================

# Initialize the chatbot instance once for the entire application
# This ensures efficient resource usage and maintains conversation state
try:
    bot = CosmosChatbot()
    print("✅ Cosmos DB Chatbot initialized successfully!")
except Exception as e:
    print(f"❌ Failed to initialize chatbot: {e}")
    print("Please check your environment configuration and try again.")
    bot = None

# ============================================================================
# Chat API Endpoints
# ============================================================================

@app.route('/api/chat', methods=['POST'])
def chat():
    """
    Process chat messages and return AI-generated responses.
    
    This endpoint handles user queries, performs vector search on uploaded documents,
    and generates contextual responses using GPT-4.
    
    Request Body:
        {
            "message": "User's question about the documents",
            "format": "standard|executive" (optional)
        }
    
    Returns:
        {
            "response": "AI-generated response with citations",
            "sources": ["list", "of", "source", "documents"],
            "chunks_used": number_of_document_chunks_used
        }
    
    Error Responses:
        400: Empty message provided
        500: Chatbot not initialized or processing error
    """
    # Validate chatbot initialization
    if not bot:
        logger.error("Chat request received but chatbot not initialized")
        return jsonify({'error': 'Chatbot not initialized'}), 500
    
    try:
        # Extract and validate request data
        data = request.json
        user_input = data.get('message', '')
        
        # Validate input is not empty
        if not user_input.strip():
            logger.warning("Empty message received in chat request")
            return jsonify({'error': 'Empty message provided'}), 400

        logger.info(f"Processing chat request: {user_input[:100]}...")
        
        # Generate AI response using the chatbot
        # This includes vector search, context retrieval, and LLM generation
        result = bot.generate_response(user_input)
        
        logger.info(f"Chat response generated successfully with {result.get('chunks_used', 0)} chunks")
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error processing chat request: {e}", exc_info=True)
        return jsonify({'error': f'Chat error: {str(e)}'}), 500

# ============================================================================
# Document Management API Endpoints
# ============================================================================

@app.route('/api/add', methods=['POST'])
def add_document():
    """
    Upload and process a new document into the knowledge base.
    
    This endpoint handles file uploads, processes the document content,
    generates embeddings, and stores everything in Cosmos DB for future retrieval.
    
    Supported file types: PDF, DOCX, PPTX, PPTM, DOCM
    
    Request: Multipart form data with 'file' field
    
    Returns:
        {
            "message": "Success message with processing details",
            "filename": "final_filename_used"
        }
    
    Error Responses:
        400: No file uploaded or no file selected
        500: Chatbot not initialized or processing error
    """
    # Validate chatbot initialization
    if not bot:
        logger.error("Document upload request received but chatbot not initialized")
        return jsonify({'error': 'Chatbot not initialized'}), 500
    
    try:
        # Validate file upload
        if 'file' not in request.files:
            logger.warning("Document upload request without file")
            return jsonify({'error': 'No file uploaded'}), 400
            
        file = request.files['file']
        if file.filename == '':
            logger.warning("Document upload request with empty filename")
            return jsonify({'error': 'No file selected'}), 400
            
        # Secure the filename to prevent path traversal attacks
        filename = secure_filename(file.filename)
        logger.info(f"Processing document upload: {filename}")
        
        # Prepare permanent storage location
        data_dir = bot.data_directory
        os.makedirs(data_dir, exist_ok=True)
        permanent_path = os.path.join(data_dir, filename)
        
        # Handle duplicate filenames by appending counter
        counter = 1
        base_name, ext = os.path.splitext(filename)
        while os.path.exists(permanent_path):
            new_filename = f"{base_name}_{counter}{ext}"
            permanent_path = os.path.join(data_dir, new_filename)
            filename = new_filename
            counter += 1
        
        # Save file permanently for future PowerPoint generation
        file.save(permanent_path)
        logger.info(f"Document saved permanently to: {permanent_path}")
        
        # Process the document: extract text, create chunks, generate embeddings
        result = bot.add_document(permanent_path, filename)
        
        logger.info(f"Document processing completed: {result}")
        return jsonify({'message': result, 'filename': filename})
        
    except Exception as e:
        logger.error(f"Error processing document upload: {e}", exc_info=True)
        return jsonify({'error': f'Document upload error: {str(e)}'}), 500

@app.route('/api/list', methods=['GET'])
def list_documents():
    """
    Retrieve a list of all documents in the knowledge base.
    
    Returns metadata about all uploaded documents including filename,
    file type, chunk count, and upload timestamp.
    
    Returns:
        {
            "documents": [
                {
                    "filename": "document.pdf",
                    "file_type": "pdf",
                    "chunk_count": 15,
                    "created_at": "2024-01-01T12:00:00"
                },
                ...
            ]
        }
    
    Error Responses:
        500: Chatbot not initialized or database error
    """
    # Validate chatbot initialization
    if not bot:
        logger.error("List documents request received but chatbot not initialized")
        return jsonify({'error': 'Chatbot not initialized'}), 500
    
    try:
        # Retrieve document list from the knowledge base
        docs = bot.list_documents()
        logger.info(f"Retrieved {len(docs)} documents from knowledge base")
        return jsonify({'documents': docs})
        
    except Exception as e:
        logger.error(f"Error listing documents: {e}", exc_info=True)
        return jsonify({'error': f'List documents error: {str(e)}'}), 500

@app.route('/api/delete', methods=['POST'])
def delete_document():
    """
    Delete a document from the knowledge base.
    
    Removes the document and all its associated chunks from Cosmos DB,
    and also deletes the physical file from storage.
    
    Request Body:
        {
            "filename": "document_to_delete.pdf"
        }
    
    Returns:
        {
            "message": "Successfully deleted document (X chunks)"
        }
    
    Error Responses:
        400: No filename provided
        404: Document not found
        500: Chatbot not initialized or deletion error
    """
    # Validate chatbot initialization
    if not bot:
        logger.error("Delete document request received but chatbot not initialized")
        return jsonify({'error': 'Chatbot not initialized'}), 500
    
    try:
        # Extract and validate filename
        filename = request.json.get('filename')
        if not filename:
            logger.warning("Delete request without filename")
            return jsonify({'error': 'No filename provided'}), 400
        
        logger.info(f"Processing delete request for: {filename}")
        
        # Attempt to delete the document
        result_message = bot.delete_document(filename)
        
        # Check if deletion was successful
        if "Error" in result_message:
            logger.warning(f"Document deletion failed: {result_message}")
            return jsonify({'error': result_message}), 404
        else:
            logger.info(f"Document deleted successfully: {result_message}")
            return jsonify({'message': result_message})
            
    except Exception as e:
        logger.error(f"Error deleting document: {e}", exc_info=True)
        return jsonify({'error': f'Delete document error: {str(e)}'}), 500

# ============================================================================
# Document Analysis API Endpoints
# ============================================================================

@app.route('/api/analyze', methods=['POST'])
def analyze_document_similarity():
    """
    Analyze document similarity against the existing knowledge base.
    
    This endpoint accepts a document upload and compares it against all
    documents in the knowledge base to find similar content. Useful for
    identifying duplicates or related documents before uploading.
    
    Request: Multipart form data with 'file' field
    
    Returns:
        {
            "similar_documents": [
                {
                    "filename": "similar_doc.pdf",
                    "file_type": "pdf",
                    "similarity_score": 0.85,
                    "matching_chunks": 12
                },
                ...
            ],
            "total_found": 3
        }
    
    Error Responses:
        400: No file uploaded or no file selected
        500: Chatbot not initialized or analysis error
    """
    # Validate chatbot initialization
    if not bot:
        logger.error("Document analysis request received but chatbot not initialized")
        return jsonify({'error': 'Chatbot not initialized'}), 500
    
    try:
        # Validate file upload
        if 'file' not in request.files:
            logger.warning("Document analysis request without file")
            return jsonify({'error': 'No file part in the request'}), 400
            
        file = request.files['file']
        if file.filename == '':
            logger.warning("Document analysis request with empty filename")
            return jsonify({'error': 'No file selected for analysis'}), 400

        # Secure the filename
        filename = secure_filename(file.filename)
        logger.info(f"Analyzing document similarity: {filename}")
        
        # Use temporary file for analysis (don't save permanently)
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[1]) as tmp:
            file.save(tmp.name)
            
            # Perform similarity analysis against knowledge base
            analysis_result = bot.find_similar_documents(tmp.name)
            
        # Clean up temporary file
        os.remove(tmp.name)
        
        logger.info(f"Similarity analysis completed for {filename}")
        return jsonify(analysis_result)
        
    except Exception as e:
        logger.error(f"Error analyzing document similarity: {e}", exc_info=True)
        return jsonify({'error': f'Analysis error: {str(e)}'}), 500

# ============================================================================
# PowerPoint Generation API Endpoints
# ============================================================================

@app.route('/api/generate-ppt', methods=['POST'])
def generate_presentation_from_text():
    """
    Generate PowerPoint presentation from current conversation context.
    
    This endpoint creates a PowerPoint presentation based on the current
    conversation, including source references and actual slide copying
    when COM integration is available on Windows.
    
    Request Body (optional):
        {
            "query": "Optional specific query to generate presentation for"
        }
    
    Returns:
        {
            "message": "Presentation generated successfully",
            "presentation_path": "/path/to/generated.pptx",
            "download_url": "/api/download-ppt?file=generated.pptx"
        }
    
    Error Responses:
        400: No valid source references found for presentation
        500: Chatbot not initialized or generation error
    """
    # Validate chatbot initialization
    if not bot:
        logger.error("PPT generation request received but chatbot not initialized")
        return jsonify({'error': 'Chatbot not initialized'}), 500

    try:
        # Extract optional query parameter
        data = request.json or {}
        query = data.get('query', '')
        
        logger.info(f"Generating presentation for query: {query[:100] if query else 'current conversation'}")
        
        # Generate presentation from current conversation or provided query
        ppt_path = bot.generate_presentation(query if query else None)
        
        if ppt_path:
            # Presentation generated successfully
            download_filename = os.path.basename(ppt_path)
            logger.info(f"Presentation generated successfully: {download_filename}")
            
            return jsonify({
                'message': 'Presentation generated successfully',
                'presentation_path': ppt_path,
                'download_url': f'/api/download-ppt?file={download_filename}'
            })
        else:
            # Failed to generate presentation - provide detailed error info
            conv_info = bot.get_conversation_info()
            error_details = (
                f'No valid source references found. '
                f'Current conversation has {conv_info.get("source_count", 0)} sources.'
            )
            
            logger.warning(f"PPT generation failed: {error_details}")
            return jsonify({
                'error': 'Could not generate presentation',
                'details': error_details,
                'conversation_info': conv_info
            }), 400

    except Exception as e:
        logger.error(f"PPT generation error: {e}", exc_info=True)
        return jsonify({
            'error': f'PPT generation error: {str(e)}',
            'details': 'Failed to generate presentation.'
        }), 500

@app.route('/api/download-ppt', methods=['GET'])
def download_ppt():
    """
    Download a generated PowerPoint presentation.
    
    This endpoint serves generated PowerPoint files for download with
    proper security checks to prevent unauthorized file access.
    
    Query Parameters:
        file: Filename of the presentation to download (must be .pptx)
    
    Returns:
        Binary PowerPoint file for download
    
    Error Responses:
        400: No file specified or invalid file type
        404: File not found
        500: Chatbot not initialized or download error
    """
    # Validate chatbot initialization
    if not bot:
        logger.error("PPT download request received but chatbot not initialized")
        return jsonify({'error': 'Chatbot not initialized'}), 500
    
    try:
        # Extract and validate filename parameter
        filename = request.args.get('file')
        if not filename:
            logger.warning("PPT download request without filename")
            return jsonify({'error': 'No file specified'}), 400
        
        # Security checks to prevent path traversal and unauthorized access
        if not filename.endswith('.pptx') or '..' in filename:
            logger.warning(f"Invalid file requested for download: {filename}")
            return jsonify({'error': 'Invalid file'}), 400
        
        # Construct secure file path within generated presentations directory
        file_path = os.path.join(bot.data_directory, 'generated_presentations', filename)
        
        # Verify file exists
        if not os.path.exists(file_path):
            logger.warning(f"Requested file not found: {file_path}")
            return jsonify({'error': 'File not found'}), 404
        
        logger.info(f"Serving PowerPoint download: {filename}")
        
        # Serve file with proper MIME type and download headers
        return send_file(
            file_path,
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.presentationml.presentation'
        )
        
    except Exception as e:
        logger.error(f"PPT download error: {e}", exc_info=True)
        return jsonify({'error': f'Download error: {str(e)}'}), 500

# ============================================================================
# Web Interface and Utility Endpoints
# ============================================================================

@app.route('/')
def root():
    """
    Serve the main web interface.
    
    Returns the HTML interface for the Document Chat Assistant,
    providing a user-friendly way to interact with the API.
    """
    return send_from_directory('static', 'index.html')

# ============================================================================
# Conversation Management API Endpoints
# ============================================================================

@app.route('/api/conversation-info', methods=['GET'])
def get_conversation_info():
    """
    Get information about the current conversation context.
    
    Returns metadata about the active conversation including query,
    source count, and presentation generation readiness.
    
    Returns:
        {
            "has_conversation": true,
            "query": "Current user query",
            "response_length": 1500,
            "source_count": 3,
            "reference_count": 5,
            "chunks_used": 10
        }
    
    Error Responses:
        500: Chatbot not initialized or error retrieving info
    """
    # Validate chatbot initialization
    if not bot:
        logger.error("Conversation info request received but chatbot not initialized")
        return jsonify({'error': 'Chatbot not initialized'}), 500
    
    try:
        # Get current conversation metadata
        info = bot.get_conversation_info()
        logger.debug("Retrieved conversation info successfully")
        return jsonify(info)
        
    except Exception as e:
        logger.error(f"Error getting conversation info: {e}", exc_info=True)
        return jsonify({'error': f'Error getting conversation info: {str(e)}'}), 500

@app.route('/api/clear-conversation', methods=['POST'])
def clear_conversation():
    """
    Clear the current conversation context.
    
    Resets the conversation state, removing all context and source references.
    This is useful for starting fresh conversations or clearing memory.
    
    Returns:
        {
            "message": "Current conversation cleared successfully"
        }
    
    Error Responses:
        500: Chatbot not initialized or error clearing conversation
    """
    # Validate chatbot initialization
    if not bot:
        logger.error("Clear conversation request received but chatbot not initialized")
        return jsonify({'error': 'Chatbot not initialized'}), 500
    
    try:
        # Clear the conversation context
        bot.clear_conversation()
        logger.info("Conversation context cleared successfully")
        return jsonify({'message': 'Current conversation cleared successfully'})
        
    except Exception as e:
        logger.error(f"Error clearing conversation: {e}", exc_info=True)
        return jsonify({'error': f'Error clearing conversation: {str(e)}'}), 500

# ============================================================================
# System Health and Monitoring Endpoints
# ============================================================================

@app.route('/health')
def health_check():
    """
    System health check endpoint.
    
    Provides comprehensive status information about the application
    including chatbot initialization, feature availability, and system capabilities.
    
    Returns:
        {
            "status": "healthy",
            "chatbot_initialized": true,
            "com_available": true,
            "features": {
                "cosmos_database": true,
                "document_processing": true,
                "presentation_generation": true,
                "multi_format_support": ["pdf", "docx", "pptx"]
            }
        }
    """
    try:
        # Gather system status information
        health_status = {
            'status': 'healthy',
            'version': '3.0',
            'chatbot_initialized': bot is not None,
            'api_key_configured': bool(os.getenv("OPENAI_API_KEY")),
            'cosmos_db_configured': bool(os.getenv("COSMOS_DB_CONNECTION_STRING")),
            'features': {
                'cosmos_database': bot is not None,
                'document_processing': True,
                'presentation_generation': bot.presentation_generator.com_available if bot else False,
                'multi_format_support': ['pdf', 'docx', 'pptx', 'pptm', 'docm'],
                'vector_search': bot is not None,
                'ai_chat': bot is not None
            }
        }
        
        # Add COM availability if chatbot is initialized
        if bot:
            health_status['com_available'] = bot.presentation_generator.com_available
        
        logger.debug("Health check completed successfully")
        return jsonify(health_status)
        
    except Exception as e:
        logger.error(f"Error during health check: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'error': str(e),
            'chatbot_initialized': False
        }), 500

# ============================================================================
# Application Entry Point
# ============================================================================

if __name__ == '__main__':
    """
    Main application entry point.
    
    Starts the Flask development server with debug mode enabled.
    In production, use a proper WSGI server like Gunicorn or uWSGI.
    """
    print("🚀 Starting Enhanced Document Chat Assistant API v3.0")
    print("=" * 60)
    print("📍 Server will be available at: http://127.0.0.1:5000")
    print("📚 Upload documents and start chatting!")
    print("🔧 Press Ctrl+C to stop the server")
    print("=" * 60)
    
    # Start the Flask development server
    app.run(
        debug=True,          # Enable debug mode for development
        port=5000,           # Standard port for the application
        host='127.0.0.1'     # Bind to localhost only for security
    )