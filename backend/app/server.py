from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit
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
socketio = SocketIO(app, cors_allowed_origins="*")  # Add this line
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
dbs=[]

def extract_text_from_image_stream(image_stream):
    image = Image.open(image_stream)
    text = pytesseract.image_to_string(image, lang="eng")
    return text
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

def process_pdf_from_memory_multiple(file_storages, text, image_storages):
    global db

    for file_storage in file_storages:
        all_docs = []
        pdf_stream = io.BytesIO(file_storage.read())
        doc = fitz.open(stream=pdf_stream, filetype="pdf")

        is_scanned = True
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            page_text = page.get_text()
            if page_text.strip():
                is_scanned = False
                break

        pdf_stream.seek(0)  # Reset stream to read again

        if is_scanned:
            print(f"Processing {file_storage.filename} as scanned PDF (OCR)...")
            extracted = extract_text_scanned_doc_from_stream(pdf_stream)
            data = text_splitter.split_text("".join(extracted.values()))
            docs = [Document(page_content=chunk) for chunk in data]
            all_docs.extend(docs)
            
        else:
            print(f"Processing {file_storage.filename} as typed PDF...")
            doc = fitz.open(stream=pdf_stream, filetype="pdf")  # reload it
            all_text = []
            for page in doc:
                all_text.append(page.get_text())
            chunks = text_splitter.split_text("".join(all_text))
            docs = [Document(page_content=chunk) for chunk in chunks]
            all_docs.extend(docs)
        dbs.append(FAISS.from_documents(documents=all_docs, embedding=embeddings))
    if text != "":
        data = text_splitter.split_text(text)
        docs_text = [Document(page_content=chunk) for chunk in data]
        dbs.append(FAISS.from_documents(documents=docs_text, embedding=embeddings))
    for image_storage in image_storages:
        image_stream = io.BytesIO(image_storage.read())
        extracted_text = extract_text_from_image_stream(image_stream)
        if extracted_text:
            data = text_splitter.split_text(extracted_text)
            docs = [Document(page_content=chunk) for chunk in data]
            dbs.append(FAISS.from_documents(documents=docs, embedding=embeddings))

# Endpoint: Upload PDF
@app.route("/upload", methods=["POST"])
def upload_pdf():
    files = request.files.getlist("pdf")
    images = request.files.getlist("image")
    text = request.form.get("text", "")
    if not files and not images and not text.strip():
        return jsonify({"error": "No PDF(s), image(s), or text uploaded"}), 400

    process_pdf_from_memory_multiple(files, text=text, image_storages=images)
    return jsonify({"message": f"{len(files)} PDF(s), {len(images)} image(s), and text processed successfully."})

@app.route("/ask", methods=["POST"])
def ask_question():
    query = request.json.get("query", "")
    if not query:
        return jsonify({"error": "Query required"}), 400

    best_score = float("inf")
    best_context = []
    best_docs = []

    for single_db in dbs:
        docs = single_db.similarity_search_with_score(query, k=2)
        
        best_context.append("\n\n".join(doc.page_content for doc, _ in docs))

    if not best_context:
        return jsonify({"response": "No relevant context found.", "chat_history": chat_history})

    prompt = f"""You are a helpful assistant. Use the following context and conversation to answer the question.

Context:
{best_context}

Conversation:
{chat_history}

Question:
{query}"""

    response = model.generate_content(prompt)
    answer = response.text

    chat_history.append({"query": query, "response": answer})

    return jsonify({"response": answer, "chat_history": chat_history})

@socketio.on('chat_message')
def handle_chat_message(data):
    query = data.get("query", "")
    if not query:
        emit('chat_response', {"error": "Query required"})
        return

    best_score = float("inf")
    best_context = []
    best_docs = []

    for single_db in dbs:
        docs = single_db.similarity_search_with_score(query, k=2)
        best_context.append("\n\n".join(doc.page_content for doc, _ in docs))

    if not best_context:
        emit('chat_response', {"response": "No relevant context found.", "chat_history": chat_history})
        return

    prompt = f"""You are a helpful assistant. Use the following context and conversation to answer the question.

Context:
{best_context}

Conversation:
{chat_history}

Question:
{query}"""

    response = model.generate_content(prompt)
    answer = response.text

    chat_history.append({"query": query, "response": answer})

    emit('chat_response', {"response": answer, "chat_history": chat_history})

if __name__ == "__main__":
    socketio.run(app, debug=True)
