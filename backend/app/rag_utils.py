import fitz  # PyMuPDF
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
import requests
import os
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

load_dotenv()
API_KEY = os.getenv("MISTRAL_API_KEY")


# 📘 Extract full PDF text
def extract_text_from_pdf(pdf_bytes):
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    return "".join(page.get_text() for page in doc)


# 📘 Chunk PDF text
def chunk_text(text):
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
    return splitter.split_text(text)


# 📘 Create vector store for retrieval
def create_vectorstore(chunks):
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2", model_kwargs={"device": "cpu"})
    return Chroma.from_texts(chunks, embedding=embeddings), embeddings


# 📘 Get relevant context (with score threshold)
def get_context(question, vectorstore, threshold=0.4):
    docs_and_scores = vectorstore.similarity_search_with_relevance_scores(question, k=3)
    filtered = [doc for doc, score in docs_and_scores if score >= threshold]
    print(f"[DEBUG] Filtered {len(filtered)} docs with score ≥ {threshold}")
    return "\n".join([doc.page_content for doc in filtered]), len(filtered)


# 📘 Check if question is semantically similar to the PDF
def is_question_related(question, pdf_text, embed_model, threshold=0.40):
    question_emb = embed_model.embed_query(question)
    pdf_emb = embed_model.embed_query(pdf_text[:1000])  # first 1000 chars to get product theme

    sim = cosine_similarity([question_emb], [pdf_emb])[0][0]
    print(f"[SEMANTIC] Similarity score: {sim:.2f}")
    return sim >= threshold


# 📘 Call Mistral
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
    print("[MISTRAL] Sending prompt to OpenRouter...")
    response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=body)
    return response.json()['choices'][0]['message']['content']


# 🌐 Web scraping fallback
def scrape_web(question):
    print("[SCRAPE] Triggered fallback search using DuckDuckGo")
    summaries = []
    with DDGS() as ddgs:
        results = list(ddgs.text(question, max_results=3))
        print(f"[SCRAPE] Found {len(results)} search results")
        for r in results:
            url = r.get("href")
            print(f"[SCRAPE] Scraping URL: {url}")
            try:
                html = requests.get(url, timeout=5).text
                soup = BeautifulSoup(html, "html.parser")
                text = soup.get_text(separator=" ", strip=True)
                summaries.append(text[:500])
            except Exception as e:
                print(f"[SCRAPE] Error scraping {url}: {e}")
                continue
    return "\n".join(summaries[:2]) or "No reliable web content found."


# 🧠 Core RAG logic
def process_pdf_and_answer(pdf_bytes, question, use_web_fallback=False):
    text = extract_text_from_pdf(pdf_bytes)
    chunks = chunk_text(text)
    vectorstore, embed_model = create_vectorstore(chunks)
    context, match_count = get_context(question, vectorstore)

    print(f"[INFO] Match count from vector DB: {match_count}")
    print(f"[INFO] use_web_fallback = {use_web_fallback}")

    # ➕ Web fallback only if semantically relevant
    if match_count < 1 and use_web_fallback:
        if is_question_related(question, text, embed_model):
            print("[INFO] Triggering web scrape fallback...")
            context = scrape_web(question)
            return call_mistral(question, context)
        else:
            print("[INFO] Question not related. Skipping fallback.")
            return (
                "Your question does not seem related to the uploaded product manual. "
                "Please ask something relevant to the product."
            )

    # ✋ No fallback allowed
    if match_count < 1 and not use_web_fallback:
        return (
            "The provided context does not contain any relevant information, "
            "and web fallback is disabled. Try uploading a different file or enable web fallback."
        )

    # ✅ Match found in PDF
    return call_mistral(question, context)
