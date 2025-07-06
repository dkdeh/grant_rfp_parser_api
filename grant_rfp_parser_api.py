from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
import pdfplumber
import openai
import os

from typing import List

app = FastAPI()

openai.api_key = os.getenv("OPENAI_API_KEY")  # Set this in your Railway environment

CHUNK_SIZE = 1000  # Adjust based on token limits

def chunk_text(text: str, size: int = CHUNK_SIZE) -> List[str]:
    words = text.split()
    return [" ".join(words[i:i + size]) for i in range(0, len(words), size)]

def extract_text_from_pdf(pdf_file) -> str:
    text = ""
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            text += page.extract_text(x_tolerance=1) + "\n"
    return text

def summarize_chunk(chunk: str) -> str:
    prompt = f"""
    You are a grant analyst AI. Summarize the following chunk of a grant RFP document.
    Extract and return key items: Title, Deadline, Eligibility, Purpose, Evaluation Criteria, Attachments Required.

    Chunk:
    {chunk}

    Respond in JSON format.
    """

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You summarize grant RFP documents."},
            {"role": "user", "content": prompt}
        ]
    )
    return response['choices'][0]['message']['content']

@app.post("/summarize-rfp")
async def summarize_rfp(file: UploadFile = File(...)):
    try:
        with open(file.filename, "wb") as f:
            content = await file.read()
            f.write(content)

        full_text = extract_text_from_pdf(file.filename)
        chunks = chunk_text(full_text)

        summaries = [summarize_chunk(chunk) for chunk in chunks[:5]]  # limit to 5 for cost control

        return JSONResponse(content={"summaries": summaries})

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
from fastapi import FastAPI, UploadFile, File, HTTPException
import traceback

@app.post("/summarize-rfp")
async def summarize_rfp(file: UploadFile = File(...)):
    try:
        print("✅ Received file:", file.filename)
        content = await file.read()

        # Decode the uploaded file to text
        text = content.decode("utf-8", errors="ignore")
        print("✅ Text decoded. Preview:")
        print(text[:300])

        # TEMP: Just return a placeholder summary
        return {"summary": "✅ This is a test summary placeholder."}

    except Exception as e:
        print("❌ Internal Server Error during summarization:")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Internal server error")
Add debug logs to summarize-rfp route
