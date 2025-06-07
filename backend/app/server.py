from flask import Flask, request, jsonify
import os
import fitz  # PyMuPDF
from werkzeug.utils import secure_filename

from langchain.vectorstores import FAISS
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document

import pytesseract
from PIL import Image
import cv2
import io
import numpy as np

import google.generativeai as genai
from flask_cors import CORS
app = Flask(__name__)
CORS(app)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Configure embeddings and model
embeddings = HuggingFaceEmbeddings()
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200, add_start_index=True)

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
genai.configure(api_key="AIzaSyBH6hVJYI6XHlIdmeYcBn4UlPmUWL233aU")
model = genai.GenerativeModel("gemini-2.0-flash")

# Global chat history
chat_history = []

# Helper: Check if PDF is scanned
def is_scanned_pdf(file_path):
    doc = fitz.open(file_path)
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        text = page.get_text()
        if text.strip():
            return False
    return True

def extract_text_scanned_doc_from_stream(pdf_stream):
    doc = fitz.open(stream=pdf_stream, filetype="pdf")
    text_data = {}

    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        pix = page.get_pixmap()
        img_bytes = pix.tobytes("png")
        pil_img = Image.open(io.BytesIO(img_bytes))
        image = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        _, im_bw = cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

        text_data[page_num + 1] = pytesseract.image_to_string(im_bw, lang="eng")
        print("1")
    return text_data

def process_pdf_from_memory(file_storage):
    global db

    pdf_stream = io.BytesIO(file_storage.read())
    doc = fitz.open(stream=pdf_stream, filetype="pdf")

    is_scanned = True
    docs = []

    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        text = page.get_text()
        if text.strip():
            is_scanned = False
            break

    pdf_stream.seek(0)  # Reset stream to read again

    if is_scanned:
        print("Processing as scanned PDF (OCR)...")
        extracted = extract_text_scanned_doc_from_stream(pdf_stream)
        data = text_splitter.split_text("".join(extracted.values()))
        print(2)
        docs = [Document(page_content=chunk) for chunk in data]
    else:
        print("Processing as typed PDF...")
        doc = fitz.open(stream=pdf_stream, filetype="pdf")  # reload it
        all_text = []
        for page in doc:
            all_text.append(page.get_text())
        chunks = text_splitter.split_text("".join(all_text))
        docs = [Document(page_content=chunk) for chunk in chunks]

    db = FAISS.from_documents(documents=docs, embedding=embeddings)



# Endpoint: Upload PDF
@app.route("/upload", methods=["POST"])
def upload_pdf():
    if "pdf" not in request.files:
        return jsonify({"error": "No PDF uploaded"}), 400

    file = request.files["pdf"]
    process_pdf_from_memory(file)

    return jsonify({"message": "PDF processed successfully."})

# Endpoint: Ask a question
@app.route("/ask", methods=["POST"])
def ask_question():
    query = request.json.get("query", "")
    if not query:
        return jsonify({"error": "Query required"}), 400

    docs = db.similarity_search_with_score(query, k=2)
    context_str = "\n\n".join(doc.page_content for doc, _ in docs)

    prompt = f"""pretend like you are a chatbot which takes context and query and you Answer using these verified sources(context):

Sources:
{context_str}
Your conversation:
{chat_history}
Question:
{query}"""

    response = model.generate_content(prompt)
    answer = response.text

    # Maintain chat history
    chat_history.append({"query": query, "response": answer})

    return jsonify({"response": answer, "chat_history": chat_history})

if __name__ == "__main__":
    app.run(debug=True)
