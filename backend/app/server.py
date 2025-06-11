from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit
import os
import fitz 
from process_pdf_files import process_pdf_from_memory_multiple, dbs
import pytesseract
from LLM_response import get_gemini_answer

from flask_cors import CORS
app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")  # Add this line
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

chat_history = []
def is_scanned_pdf(file_path):
    doc = fitz.open(file_path)
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        text = page.get_text()
        if text.strip():
            return False
    return True



# Endpoint: Upload PDF
@app.route("/upload", methods=["POST"])
def upload_pdf():
    files = request.files.getlist("pdf")
    images = request.files.getlist("image")
    text = request.form.get("text", "")
    if not files and not images and not text.strip():
        return jsonify({"error": "No PDF(s), image(s), or text uploaded"}), 400

    process_pdf_from_memory_multiple(files, text=text, image_storages=images, pytesseract=pytesseract)
    return jsonify({"message": f"{len(files)} PDF(s), {len(images)} image(s), and text processed successfully."})


@socketio.on('chat_message')
def handle_chat_message(data):
    query = data.get("query", "")
    if not query:
        emit('chat_response', {"error": "Query required"})
        return

    all_results = []

    for single_db in dbs:
        docs = single_db.similarity_search_with_score(query, k=1)
        for doc, score in docs:
            if score<1:
                all_results.append((doc, score))

    # Sort all results by score (lower is better for similarity)
    all_results.sort(key=lambda x: x[1])

    # Take top 2
    top_results = all_results

    best_context = [doc.page_content for doc, _ in top_results]
    best_sources = [doc.metadata for doc, _ in top_results]

    if len(best_context)==0:
        emit('chat_response', {"response": "No relevant context found.", "chat_history": chat_history})
        return

    answer =get_gemini_answer(best_context , chat_history , query)

    chat_history.append({"query": query, "response": answer})
    
    emit('chat_response', {
        "response": answer,
        "chat_history": chat_history,
        "sources": best_sources ,
        "context":best_context
    })

if __name__ == "__main__":
    socketio.run(app, debug=True)
