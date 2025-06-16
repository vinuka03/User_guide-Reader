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

load_dotenv()
API_KEY = os.getenv("MISTRAL_API_KEY")

# 📘 Extract text from PDF
def extract_text_from_pdf(pdf_bytes):
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    return "".join(page.get_text() for page in doc)

# 📘 Chunk into passages
def chunk_text(text):
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
    return splitter.split_text(text)

# 📘 Convert to vector store
def create_vectorstore(chunks, embeddings):
    return Chroma.from_texts(chunks, embedding=embeddings)

# 📘 Retrieve relevant context + score
def get_context(question, vectorstore, threshold=0.4):
    docs_and_scores = vectorstore.similarity_search_with_relevance_scores(question, k=3)
    filtered = [doc for doc, score in docs_and_scores if score >= threshold]
    print(f"[DEBUG] Filtered {len(filtered)} docs with score ≥ {threshold}")
    return "\n".join([doc.page_content for doc in filtered]), len(filtered)

# 📘 Call Mistral via OpenRouter API
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

# 🧠 Semantic check using all chunks
def is_question_related(question, chunks, embeddings, threshold=0.4):
    question_emb = embeddings.embed_query(question)
    chunk_embs = [embeddings.embed_query(c) for c in chunks]
    sims = cosine_similarity([question_emb], chunk_embs)[0]
    max_sim = max(sims)
    print(f"[SEMANTIC] Max similarity score across all chunks: {max_sim:.2f}")
    return max_sim >= threshold

# 🧠 Main PDF + web fallback logic
def process_pdf_and_answer(pdf_bytes, question, use_web_fallback=False):
    text = extract_text_from_pdf(pdf_bytes)
    chunks = chunk_text(text)
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2", model_kwargs={"device": "cpu"})
    vectorstore = create_vectorstore(chunks, embeddings)
    context, match_count = get_context(question, vectorstore)

    print(f"[INFO] Match count from vector DB: {match_count}")
    print(f"[INFO] use_web_fallback = {use_web_fallback}")

    if match_count < 1:
        if use_web_fallback:
            if is_question_related(question, chunks, embeddings):
                print("[INFO] Triggering web scrape fallback...")
                context = scrape_web(question)
                return call_mistral(question, context), "web"  # ✅ Web fallback, label as "web"
            else:
                print("[INFO] Question not related. Skipping fallback.")
                return (
                    "Your question does not seem related to the uploaded product manual. Please ask something relevant to the product.",
                    "none"
                )
        else:
            print("[INFO] No match & fallback disabled. Returning static message.")
            return (
                "The provided context does not contain any relevant information, "
                "and web fallback is disabled. Try uploading a different file or enable web fallback.",
                "none"
            )

    return call_mistral(question, context), "pdf"  # ✅ Direct PDF match
