from fastapi import FastAPI, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from app.rag_utils import process_pdf_and_answer
from fastapi import FastAPI, UploadFile, Form
from fastapi.responses import JSONResponse

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/ask")
async def ask(file: UploadFile, question: str = Form(...), use_web_fallback: str = Form("false")):
    pdf_bytes = await file.read()
    answer, source = process_pdf_and_answer(pdf_bytes, question, use_web_fallback == "true")
    return JSONResponse(content={"answer": answer, "source": source})
