import os
from typing import List
from PyPDF2 import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from fastapi import FastAPI, File, UploadFile
import google.generativeai as genai
from langchain_community.vectorstores import FAISS
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains.question_answering import load_qa_chain
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from concurrent.futures import ThreadPoolExecutor
import asyncio

class QuestionRequest(BaseModel):
    question: str

load_dotenv()
os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# SQLite database initialization
# conn = sqlite3.connect('pdfs.db')
# c = conn.cursor()
# c.execute('''
#     CREATE TABLE IF NOT EXISTS pdfs (
#         id INTEGER PRIMARY KEY,
#         filename TEXT,
#         upload_date TEXT,
#         text TEXT
#     )
# ''')
# conn.commit()

# read all pdf files and return text

def get_pdf_text(pdf_docs):
    text = ""
    # conn = sqlite3.connect('pdfs.db')
    # c = conn.cursor()
    
    for pdf in pdf_docs:
        pdf_reader = PdfReader(pdf.file)
        for page in pdf_reader.pages:
            text += page.extract_text()

        # Store PDF details in the database
        # filename = pdf.filename
    #     upload_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    #     c.execute("INSERT INTO pdfs (filename, upload_date, text) VALUES (?, ?, ?)", (filename, upload_date, text))

    # conn.commit()
    # conn.close() 
    return text

# split text into chunks
def get_text_chunks(text):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=10000, chunk_overlap=1000)
    chunks = splitter.split_text(text)
    return chunks  # list of strings

# get embeddings for each chunk
def get_vector_store(chunks):
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/embedding-001")  # type: ignore
    vector_store = FAISS.from_texts(chunks, embedding=embeddings)
    vector_store.save_local("faiss_index")

def get_conversational_chain():
    prompt_template = """
    Answer the question as detailed as possible from the provided context, make sure to provide all the details, if the answer is not in
    provided context just say, "answer is not available in the context", don't provide the wrong answer\n\n
    Context:\n {context}?\n
    Question: \n{question}\n

    Answer:
    """

    model = ChatGoogleGenerativeAI(model="gemini-1.5-flash-latest",
                                   client=genai,
                                   temperature=0.3,
                                   ) #type:ignore
    prompt = PromptTemplate(template=prompt_template,
                            input_variables=["context", "question"])
    chain = load_qa_chain(llm=model, chain_type="stuff", prompt=prompt)
    return chain

def user_input(user_question):
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/embedding-001")  # type: ignore

    new_db = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True) 
    docs = new_db.similarity_search(user_question)

    chain = get_conversational_chain()

    response = chain(
        {"input_documents": docs, "question": user_question}, return_only_outputs=True, )

    print(response)
    return response

def process_pdf_files(files):
    raw_text = get_pdf_text(files)
    text_chunks = get_text_chunks(raw_text)
    get_vector_store(text_chunks)
    return {"message": "PDFs uploaded and processed successfully"}


@app.get("/")
async def root():
    return {"greeting": "Hello, World!", "message": "Welcome to FastAPI!"}
@app.post("/upload")
async def upload_pdf_files(files: List[UploadFile] = File(...)):
    if not files:
        return {"error": "No files uploaded"}
    for file in files:
        print(f"Received file: {file.filename}")
    
    # Process PDFs asynchronously
    with ThreadPoolExecutor() as executor:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(executor, process_pdf_files, files)
    
    return {"message": "PDFs uploaded and processing"}

@app.post("/ask")
async def ask_question(request: QuestionRequest):
    response = user_input(request.question)
    return {"answer": response['output_text']}
