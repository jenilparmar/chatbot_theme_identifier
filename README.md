# Chatbot Theme Identifier

A full-stack AI-powered chatbot that allows users to upload PDFs, images, or text, ask questions, and receive answers with cited sources and synthesized themes. The app supports document selection, context highlighting,  loading animation, read-aloud functionality

---

## Features

- **Multi-file Upload:** Upload PDFs (typed or scanned), images, and/or enter text.
- **Selective Search:** Choose which uploaded files to include/exclude from search via checkboxes.
- **Document Preview:** Preview PDFs and images in-app.
- **Contextual Q&A:** Ask questions and get answers with cited sources and extracted context.
- **Synthesized Theme Answers:** See both individual document answers (tabular) and a synthesized, theme-based summary.
- **Source Navigation:** Click citations to jump to the relevant file and page.
- **Expandable Context:** Expand/collapse extracted context for easier reading.
- **Read Aloud:** Listen to answers with play, pause, resume, and stop controls.
- **Modern UI:** Responsive, accessible, and styled with Tailwind CSS and React Icons.

---

## Tech Stack

- **Frontend:** Next.js (with hooks), Tailwind CSS, React Icons, ReactMarkdown
- **Backend:** Flask, Flask-SocketIO, SentenceTransformers (all-MiniLM-L6-v2), PyMuPDF, FAISS
- **Vector Search:** FAISS 
- **OCR:** pytesseract (for scanned PDFs and images)
- **WebSocket:** Real-time Q&A via Flask-SocketIO

---

## Getting Started

### Prerequisites

- Node.js & npm
- Python 3.8+
- pip

### Backend Setup

1. **Install dependencies:**
    ```sh
    pip install -r requirements.txt
    ```

2. **Run the backend:**
    ```sh
    python backend/app/server.py
    ```

### Frontend Setup

1. **Install dependencies:**
    ```sh
    cd frontend/my-app
    npm install
    ```

2. **Run the frontend:**
    ```sh
    npm run dev
    ```

3. **Access the app:**  
   Open [http://localhost:3000](http://localhost:3000) in your browser.

---

## Usage

1. **Upload** PDFs, images, or enter text.
2. **Select** which files to include in search using checkboxes.
3. **Ask** a question in the chat box.
4. **View** answers with cited sources and synthesized themes.
5. **Click** citations to jump to the relevant file/page.
6. **Expand** context for detailed view.
7. **Listen** to answers using the read-aloud controls.

---

## Example Output

| Document ID | Extracted Answer                                 | Citation         |
|-------------|--------------------------------------------------|------------------|
| DOC001      | The order states that the fine was imposed...    | Page 4, Para 2   |
| DOC002      | Tribunal observed delay in disclosure...         | Page 2, Para 1   |

---

## Project Structure

```
chatbot_theme_identifier/
├── backend/
│   └── app/
│       └── server.py
├── frontend/
│   └── my-app/
│       └── src/
│           └── app/
│               └── page.jsx
├── requirements.txt
└── README.md
```

---
