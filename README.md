# LangGraph RAG Workflow

## Overview
This project demonstrates a Retrieval-Augmented Generation (RAG) workflow for matching researcher profiles with user queries using the LangChain framework. It integrates document retrieval, a Long Language Model (LLM), and a state machine workflow to handle the entire process, from retrieving relevant researcher profiles to generating user responses.

The main components of the workflow include:
- Loading researcher profiles from a JSON file.
- Splitting the researcher data into smaller chunks for efficient retrieval.
- Creating a vector store using Chroma for document embeddings.
- Using Retrieval-Augmented Generation to answer user queries in an interactive and intelligent manner.

## Features
- Uses **Chroma** for efficient document embedding and retrieval.
- **GPT4All** embeddings for vector store creation.
- **ChatOllama** for a conversational LLM interface.
- **LangChain** for text splitting, prompt creation, and chaining LLMs.
- A **StateGraph** for defining workflow nodes and transitions for document retrieval, grading, and answer generation.

## Installation
To run this project, you need to install the required dependencies, which are listed in `requirements.txt`. Please follow these steps:

1. Clone the repository:
    ```
    git clone <repository_url>
    cd langchain_rag_workflow
    ```

2. Create a virtual environment and activate it:
    ```
    python -m venv env
    # On Windows:
    .\env\Scripts\activate
    # On macOS/Linux:
    source env/bin/activate
    ```

3. Install the required dependencies:
    ```
    pip install -r requirements.txt
    ```

4. Install and download the llama3 model using ollama:
    ```bash
    # Install ollama (if not already installed)
    curl -fsSL https://ollama.com/install.sh | sh
    
    # Download the llama3 model
    ollama pull llama3
    ```

5. Ensure you have a JSON file containing researcher profiles at the specified path (`/home/svend/projects/langgraph_advanced_RAG/researchers.json`). You can customize the JSON file location in the script.

## Usage
The application starts by prompting the user to enter a question. It then retrieves relevant researcher profiles based on the user's question, grades their relevance, and uses Retrieval-Augmented Generation (RAG) to generate an answer. Follow these steps to run the application:

1. Run the script:
    ```
    python langchain_rag_workflow.py
    ```

2. You will be prompted to enter a question:
    ```
    You: What are the researchers working on artificial intelligence?
    ```

3. The workflow will handle document retrieval, grading, and generate a relevant response with the matched researcher profiles.

## Project Structure
- **langchain_rag_workflow.py**: The main script to run the RAG workflow.
- **researchers.json**: A JSON file that contains profiles of researchers (name, bio, keywords, research unit, etc.). You can modify this file to match your data.
- **requirements.txt**: Contains all the dependencies required to run the project.

## Requirements
- Python 3.8+
- `langchain`
- `langchain_community`
- `langchain_ollama`
- `langchain_core`
- `Chroma`
- `GPT4AllEmbeddings`

Install all required packages by running:
```bash
pip install -r requirements.txt
```

## Example Workflow
The workflow includes:
1. **Retrieve**: Uses a retriever to fetch relevant documents based on the user's input.
2. **Grade Documents**: Grades the relevance of the retrieved documents.
3. **Generate**: Uses the retrieved and graded documents to generate a final response.

## License
Feel free to use and modify this project as per your requirements. Licensed under MIT.

## Contact
For any issues or questions, please reach out to me.

## Contributions
Contributions are welcome! Please open a pull request or issue for any suggestions or bug reports.

## To Do
- Add support for different types of embeddings and vector stores.
- Include a more interactive frontend interface to enhance usability.
