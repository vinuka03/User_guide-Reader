import fitz  # PyMuPDF
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
import requests
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("MISTRAL_API_KEY")

def extract_text_from_pdf(pdf_bytes):
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    return "".join(page.get_text() for page in doc)

def chunk_text(text):
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
    return splitter.split_text(text)

def create_vectorstore(chunks):
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2", model_kwargs={"device": "cpu"})
    return Chroma.from_texts(chunks, embedding=embeddings)

def get_context(question, vectorstore):
    docs = vectorstore.similarity_search(question, k=3)
    return "\n".join([doc.page_content for doc in docs])

def call_mistral(question, context):
    prompt = f"""Answer this question using the context below.

Context:
{context}

Question: {question}
"""
    headers = {"Authorization": f"Bearer {API_KEY}"}
    body = {
        "model": "meta-llama/llama-3.3-8b-instruct:free",
        "messages": [{"role": "user", "content": prompt}]
    }
    response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=body)
    return response.json()['choices'][0]['message']['content']

def process_pdf_and_answer(pdf_bytes, question):
    text = extract_text_from_pdf(pdf_bytes)
    chunks = chunk_text(text)
    vectorstore = create_vectorstore(chunks)
    context = get_context(question, vectorstore)
    return call_mistral(question, context)
