import os
from typing_extensions import TypedDict
from typing import List
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import GPT4AllEmbeddings
from langchain.prompts import PromptTemplate
from langchain_ollama import ChatOllama
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from langgraph.graph import END, StateGraph
from langchain.schema import Document

# Constants
LOCAL_LLM = 'llama3'
FOLDER_PATH = "/home/svend/projects/LAMARAG/split_files/"
CHUNK_SIZE = 250
CHUNK_OVERLAP = 0

# Load documents from the folder. Each text file is read and converted into a LangChain Document object.
def load_documents(folder_path):
    """
    Load documents from a specified folder path.
    Reads all text files in the folder, converts them into LangChain Document objects, and returns a list of these documents.

    Args:
        folder_path (str): The path to the folder containing the text files.

    Returns:
        list: A list of Document objects containing the content of each text file.
    """
    docs_list = []
    for filename in os.listdir(folder_path):
        if filename.endswith(".txt"):
            with open(os.path.join(folder_path, filename), "r", encoding="utf-8") as file:
                content = file.read()
                docs_list.append(Document(page_content=content))
    return docs_list

# Split the loaded documents into smaller chunks for better retrieval and indexing.
def split_documents(docs_list, chunk_size, chunk_overlap):
    """
    Split documents into smaller chunks for better indexing and retrieval.
    Uses a character-based splitter to divide each document into smaller parts with a specified chunk size and overlap.

    Args:
        docs_list (list): A list of Document objects to be split.
        chunk_size (int): The maximum size of each chunk in characters.
        chunk_overlap (int): The number of characters to overlap between chunks.

    Returns:
        list: A list of split Document objects.
    """
    text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        chunk_size=chunk_size, chunk_overlap=chunk_overlap
    )
    return text_splitter.split_documents(docs_list)

# Create a vector store using the Chroma library.
def create_vector_store(doc_splits):
    """
    Create a vector store using the Chroma library.
    Stores document embeddings for efficient retrieval.

    Args:
        doc_splits (list): A list of split Document objects to be indexed in the vector store.

    Returns:
        Chroma: A Chroma vector store object containing the document embeddings.
    """
    return Chroma.from_documents(
        documents=doc_splits,
        collection_name="rag-chroma",
        embedding=GPT4AllEmbeddings(),
    )

# Define a function to format retrieved documents for use as context in prompts.
def format_docs(docs):
    """
    Format a list of documents into a single string for use as context in prompts.
    Joins the content of all documents with double line breaks for better readability.

    Args:
        docs (list): A list of Document objects.

    Returns:
        str: A formatted string containing the content of all documents.
    """
    return "\n\n".join(doc.page_content for doc in docs)

# Define a function to create prompt templates.
def create_prompt_template(template_str, input_variables):
    """
    Create a prompt template for use in the LLM.
    The template defines the structure of the input, and input variables are placeholders.

    Args:
        template_str (str): The template string defining the structure of the prompt.
        input_variables (list): A list of variables that will be used in the prompt.

    Returns:
        PromptTemplate: A PromptTemplate object configured with the provided template string and input variables.
    """
    return PromptTemplate(
        template=template_str,
        input_variables=input_variables,
    )

# Load documents and create a vector store.
docs_list = load_documents(FOLDER_PATH)
doc_splits = split_documents(docs_list, CHUNK_SIZE, CHUNK_OVERLAP)
vectorstore = create_vector_store(doc_splits)
retriever = vectorstore.as_retriever()

# Create prompt templates.
retrieval_grader_prompt = create_prompt_template(
    template_str="""<|begin_of_text|><|start_header_id|>system<|end_header_id|> You are provided with a 
    researcher profile that is matched with a user query. If the profiles includes keywords associated with the query, 
    mark it as relevant. The assessment should not be overly strict; the objective is to eliminate incorrect retrievals. 
    Assign a binary score of 'yes' or 'no' to indicate the profile's relevance. 
    Return the binary score as a JSON with a single key 'score', without any preamble or further explanation.
    <|eot_id|><|start_header_id|>user<|end_header_id|>
    This is the retrieved researcher profile: \n\n {document} \n\n
    This is the user question: {question} \n <|eot_id|><|start_header_id|>assistant<|end_header_id|>
    """,
    input_variables=["question", "document"]
)

rag_generation_prompt = create_prompt_template(
    template_str="""<|begin_of_text|><|start_header_id|>system<|end_header_id|> You are an assistant for 
    question-answering tasks. Use the provided retrieved context to answer the question. 
    If the answer is not clear, simply state that you don't know. Point out why the profiles match the query. 
    End with a list of the relevant researchers with their contact information.
    Keep your response concise but complete.
    . <|eot_id|><|start_header_id|>user<|end_header_id|>
    Question: {question} 
    Context: {context} 
    Answer: <|eot_id|><|start_header_id|>assistant<|end_header_id|>""",
    input_variables=["question", "context"]
)

# Define the LLM.
llm = ChatOllama(model=LOCAL_LLM, temperature=0)

# Set up chains using prompt templates, LLM, and parsers.
retrieval_grader = retrieval_grader_prompt | llm | JsonOutputParser()
rag_chain = rag_generation_prompt | llm | StrOutputParser()

# Define the state class to represent the state of our LangChain StateGraph workflow.
class GraphState(TypedDict):
    """
    Represents the state of our graph.

    Attributes:
        question (str): The user's question.
        generation (str): The generated response from the LLM.
        documents (List[str]): A list of retrieved documents.
    """
    question : str
    generation : str
    documents : List[str]

# Define functions for different nodes in the workflow.

def retrieve(state):
    """
    Retrieve documents from the vectorstore based on the user's question.

    Args:
        state (dict): The current graph state containing the user's question.

    Returns:
        state (dict): Updated state containing the retrieved documents.
    """
    print("---RETRIEVE---")
    question = state["question"]

    # Retrieval
    documents = retriever.invoke(question)
    return {"documents": documents, "question": question}


def generate(state):
    """
    Generate an answer using Retrieval-Augmented Generation (RAG) based on the retrieved documents.

    Args:
        state (dict): The current graph state containing the user's question and retrieved documents.

    Returns:
        state (dict): Updated state containing the generated answer.
    """
    print("---GENERATE---")
    question = state["question"]
    documents = state["documents"]
    
    # RAG generation
    generation = rag_chain.invoke({"context": documents, "question": question})
    return {"documents": documents, "question": question, "generation": generation}

def grade_documents(state):
    """
    Grade the relevance of the retrieved documents to the user's question.
    If any document is not relevant, set a flag to indicate further retrieval might be needed.

    Args:
        state (dict): The current graph state containing the user's question and retrieved documents.

    Returns:
        state (dict): Updated state containing the filtered relevant documents.
    """
    print("---CHECK DOCUMENT RELEVANCE TO QUESTION---")
    question = state["question"]
    documents = state["documents"]
    
    # Score each document
    filtered_docs = []
    for d in documents:
        score = retrieval_grader.invoke({"question": question, "document": d.page_content})
        grade = score['score']
        # Document relevant
        if grade.lower() == "yes":
            print("---GRADE: DOCUMENT RELEVANT---")
            filtered_docs.append(d)
        # Document not relevant
        else:
            print("---GRADE: DOCUMENT NOT RELEVANT---")
    return {"documents": filtered_docs, "question": question}

# Create a StateGraph to define a workflow using the nodes and functions defined above.
workflow = StateGraph(GraphState)

# Add nodes to the workflow, defining the possible paths the workflow can take.
workflow.add_node("retrieve", retrieve) # Document retrieval node
workflow.add_node("grade_documents", grade_documents) # Document grading node
workflow.add_node("generate", generate) # Document generation node

# Define the entry point of the workflow.
workflow.set_entry_point("retrieve")

# Add edges to the workflow to determine which functions should run after another node completes.
workflow.add_edge("retrieve", "grade_documents")
workflow.add_edge("grade_documents", "generate")

# Compile the workflow into an application.
app = workflow.compile()

# Run the compiled application by providing a question.
# The app will stream the outputs from each function that is executed.
from pprint import pprint
inputs = {"question": "I'm looking for a computer vision engineer in the field of medical image analysis?"}
for output in app.stream(inputs):
    for key, value in output.items():
        pprint(f"Finished running: {key}:")
pprint(value["generation"])
