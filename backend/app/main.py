from fastapi import FastAPI, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from app.rag_utils import process_pdf_and_answer

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/ask")
async def ask_question(file: UploadFile, question: str = Form(...)):
    pdf_bytes = await file.read()
    answer = process_pdf_and_answer(pdf_bytes, question)
    return {"answer": answer}
