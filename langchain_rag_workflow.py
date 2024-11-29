import logging
import sys
from rag_profiles import RAGQueryEngine

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                   stream=sys.stdout)
logger = logging.getLogger(__name__)

def main():
    try:
        # Initialize RAG engine
        logger.info("Initializing RAG Query Engine...")
        rag_engine = RAGQueryEngine()
        logger.info("RAG Query Engine initialized successfully")

        # Interactive loop
        print("\nWelcome to the Researcher Profile Query System!")
        print("Enter your questions about researchers or type 'quit' to exit.\n")
        
        while True:
            # Get user input
            question = input("You: ").strip()
            
            # Check for exit condition
            if question.lower() in ['quit', 'exit', 'q']:
                print("\nThank you for using the Researcher Profile Query System!")
                break
            
            if not question:
                continue
            
            # Process question
            logger.info(f"Processing question: {question}")
            try:
                response = rag_engine.query(question)
                print("\nSystem:", response, "\n")
            except Exception as e:
                logger.error(f"Error processing question: {str(e)}")
                print("\nError: An error occurred while processing your question. Please try again.\n")

    except Exception as e:
        logger.error(f"Failed to initialize RAG Query Engine: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
