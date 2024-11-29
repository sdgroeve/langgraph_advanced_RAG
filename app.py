from flask import Flask, render_template, request, jsonify
import logging
import sys
from rag_profiles import RAGQueryEngine

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                   stream=sys.stdout)
logger = logging.getLogger(__name__)

# Initialize Flask app and RAG engine
app = Flask(__name__)
try:
    logger.info("Initializing RAG Query Engine...")
    rag_engine = RAGQueryEngine()
    logger.info("RAG Query Engine initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize RAG Query Engine: {str(e)}")
    sys.exit(1)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/ask', methods=['POST'])
def ask():
    try:
        question = request.json['question']
        logger.info(f"Received question: {question}")
        
        # Get response from RAG engine
        response = rag_engine.query(question)
        logger.info("Generated response successfully")
        
        return jsonify({'response': response})
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return jsonify({'response': f"An error occurred: {str(e)}"}), 500

if __name__ == '__main__':
    try:
        logger.info("Starting Flask application...")
        app.run(debug=True, host='127.0.0.1', port=5000)
    except Exception as e:
        logger.error(f"Failed to start Flask application: {str(e)}")
        sys.exit(1)
