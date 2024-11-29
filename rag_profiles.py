import os
import json
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
JSON_FILE_PATH = "/home/svend/projects/langgraph_advanced_RAG/scraping/researchers_crig.json"
CHUNK_SIZE = 250
CHUNK_OVERLAP = 0
EMBEDDINGS_DIR = "/home/svend/projects/langgraph_advanced_RAG/embeddings_db"

# Define the state class
class GraphState(TypedDict):
    """
    Represents the state of our graph.

    Attributes:
        question (str): The user's question.
        generation (str): The generated response from the LLM.
        documents (List[str]): A list of retrieved documents.
    """
    question: str
    generation: str
    documents: List[str]

# Load documents from the JSON file.
def load_documents_from_json(json_file_path):
    docs_list = []
    with open(json_file_path, "r", encoding="utf-8") as file:
        data = json.load(file)
        for profile in data:
            content = (
                f"Name: {profile.get('name', 'N/A')}\n"
                f"Profile URL: {profile.get('profile_url', 'N/A')}\n"
                f"Description: {profile.get('description', 'N/A')}\n"
                f"Keywords: {', '.join(profile.get('keywords', []))}\n"
                f"Research Focus: {profile.get('research_focus', 'N/A')}\n"
                f"Contact Info: {profile.get('contact_info', 'N/A')}\n"
                f"Links: {', '.join([link['text'] + ' (' + link['url'] + ')' for link in profile.get('links', [])])}"
            )
            docs_list.append(Document(page_content=content))
    return docs_list

# Split the loaded documents into smaller chunks
def split_documents(docs_list, chunk_size, chunk_overlap):
    text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        chunk_size=chunk_size, chunk_overlap=chunk_overlap
    )
    return text_splitter.split_documents(docs_list)

# Create or load a vector store using the Chroma library.
def create_vector_store(doc_splits):
    embedding_function = GPT4AllEmbeddings()
    
    # Try to load existing embeddings
    if os.path.exists(EMBEDDINGS_DIR):
        try:
            vectorstore = Chroma(
                persist_directory=EMBEDDINGS_DIR,
                embedding_function=embedding_function,
                collection_name="rag-chroma"
            )
            # If collection exists and has documents, return it
            if vectorstore._collection.count() > 0:
                return vectorstore
        except Exception as e:
            print(f"Error loading existing embeddings: {e}")
    
    # Create new embeddings if none exist or loading failed
    vectorstore = Chroma.from_documents(
        documents=doc_splits,
        embedding=embedding_function,
        persist_directory=EMBEDDINGS_DIR,
        collection_name="rag-chroma"
    )
    vectorstore.persist()
    return vectorstore

# Format documents for use as context
def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

class RAGQueryEngine:
    def __init__(self):
        # Load documents and create vector store
        self.docs_list = load_documents_from_json(JSON_FILE_PATH)
        self.doc_splits = split_documents(self.docs_list, CHUNK_SIZE, CHUNK_OVERLAP)
        self.vectorstore = create_vector_store(self.doc_splits)
        self.retriever = self.vectorstore.as_retriever()
        
        # Create prompt templates
        self.retrieval_grader_prompt = PromptTemplate(
            template="""<|begin_of_text|><|start_header_id|>system<|end_header_id|> You are provided with a \
            researcher profile that is matched with a user query. If the profiles include keywords associated with the query, \
            mark it as relevant. The assessment should not be overly strict; the objective is to eliminate incorrect retrievals. \
            Assign a binary score of 'yes' or 'no' to indicate the profile's relevance. \
            Return the binary score as a JSON with a single key 'score', without any preamble or further explanation.\n<|eot_id|><|start_header_id|>user<|end_header_id|>\nThis is the retrieved researcher profile: \n\n {document} \n\n\nThis is the user question: {question} \n<|eot_id|><|start_header_id|>assistant<|end_header_id|>""",
            input_variables=["question", "document"]
        )

        self.rag_generation_prompt = PromptTemplate(
            template="""<|begin_of_text|><|start_header_id|>system<|end_header_id|> 

You are a highly intelligent and helpful chatbot designed to match user queries 
with a provided list of researcher profiles. 
Your task is to evaluate the given profiles 
against the user query, identify relevant matches, 
and generate a detailed and structured response. 
Follow these guidelines precisely:

### Task Overview:
1. **Input:** You will be given:
   - A user query describing a topic, area of interest, or specific need.
   - A list of researcher profiles, including their expertise, fields of research, and contact information.

2. **Matching Criteria:** Match profiles to the query based on:
   - **Relevance:** The profile's expertise should align with the query. Matches can be approximate but must make sense contextually.
   - **Ranked Matches:** Rank the profiles based on the degree of relevance to the query.

3. **Response Requirements:**
   - Clearly state the matched profiles in descending order of relevance.
   - For each match, include:
     - The researcher's name.
     - Areas of expertise.
     - Reason why the profile matched the query.
     - The profile url
   - Clearly explain why each profile was considered a match.
   - If no profiles match, state explicitly: *"No profiles in the provided list match the query."*
   - Do **not** invent or fabricate profiles under any circumstances.

4. **Response Format:**
   - Use clear, professional language.
   - Structure your response with bullet points or numbered lists for clarity.

5. **Important Notes:**
   - Do not return any made-up profiles or information.
   - Always ensure that the reasons for matching a profile are logical and well-explained.
   - If the user query is vague, interpret it to the best of your ability and still adhere to the guidelines above.

If you understand, proceed to evaluate and respond based on these guidelines.
You are allowed to end with a suggestion for a beter user query if that would be approriate.

            <|eot_id|><|start_header_id|>user<|end_header_id|>            
            \nQuestion: {question} \nContext: {context} \nAnswer: <|eot_id|><|start_header_id|>assistant<|end_header_id|>""",
            input_variables=["question", "context"]
        )

        # Set up LLM and chains
        self.llm = ChatOllama(model=LOCAL_LLM, temperature=0)
        self.retrieval_grader = self.retrieval_grader_prompt | self.llm | JsonOutputParser()
        self.rag_chain = self.rag_generation_prompt | self.llm | StrOutputParser()

        # Set up workflow
        self.workflow = self._create_workflow()
        self.app = self.workflow.compile()

    def _create_workflow(self):
        workflow = StateGraph(GraphState)
        
        workflow.add_node("retrieve", self.retrieve)
        workflow.add_node("grade_documents", self.grade_documents)
        workflow.add_node("generate", self.generate)
        
        workflow.set_entry_point("retrieve")
        workflow.add_edge("retrieve", "grade_documents")
        workflow.add_edge("grade_documents", "generate")
        
        return workflow

    def retrieve(self, state):
        question = state["question"]
        documents = self.retriever.invoke(question)
        return {"documents": documents, "question": question}

    def generate(self, state):
        question = state["question"]
        documents = state["documents"]
        
        # Check if there are any relevant documents
        if not documents:
            generation = "I apologize, but I couldn't find any matching researcher profiles for your query. Please try rephrasing your question or asking about a different research topic."
        else:
            generation = self.rag_chain.invoke({"context": format_docs(documents), "question": question})
        
        return {"documents": documents, "question": question, "generation": generation}

    def grade_documents(self, state):
        question = state["question"]
        documents = state["documents"]
        filtered_docs = []
        for d in documents:
            score = self.retrieval_grader.invoke({"question": question, "document": d.page_content})
            if score['score'].lower() == "yes":
                filtered_docs.append(d)
        return {"documents": filtered_docs, "question": question}

    def query(self, question):
        inputs = {"question": question}
        final_output = None
        for output in self.app.stream(inputs):
            final_output = output
        return final_output.get('generate', {}).get('generation', '')

# Initialize the query engine if running as main
if __name__ == "__main__":
    engine = RAGQueryEngine()
    while True:
        user_question = input("You: ")
        if user_question.lower() in ['quit', 'exit']:
            break
        response = engine.query(user_question)
        print("\nAssistant:", response, "\n")
