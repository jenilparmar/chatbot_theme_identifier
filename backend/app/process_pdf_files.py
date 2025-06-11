import fitz
import io
from PIL import Image
import cv2
import numpy as np
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain.vectorstores import FAISS
text_splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=300, add_start_index=True)

from sentence_transformers import SentenceTransformer
dbs = []
sbert_model = SentenceTransformer("all-MiniLM-L6-v2")
class SBERTEmbeddings:
    def __init__(self, model):
        self.model = model

    def embed_documents(self, texts):
        return self.model.encode(texts, convert_to_tensor=False)

    def embed_query(self, text):
        return self.model.encode([text])[0]

    def __call__(self, text):
        return self.embed_query(text)  

from sentence_transformers import SentenceTransformer

sbert_model = SentenceTransformer("all-MiniLM-L6-v2")
embeddings = SBERTEmbeddings(sbert_model)
def extract_text_scanned_doc_from_stream(pdf_stream , pytesseract):
    doc = fitz.open(stream=pdf_stream, filetype="pdf")
    text_data = {}

    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        pix = page.get_pixmap()
        img_bytes = pix.tobytes("png")
        pil_img = Image.open(io.BytesIO(img_bytes))
        image = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        gray = cv2.medianBlur(gray, 3)
        _, im_bw = cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        binary = cv2.adaptiveThreshold(im_bw, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
        cv2.imwrite("deno.jpg" , binary)
        text_data[page_num + 1] = pytesseract.image_to_string(binary, lang="eng")
        # print(text_data)
        # print("1")
    return text_data

def extract_text_from_image_stream(image_stream , pytesseract):
    
    pil_image = Image.open(image_stream)
    
    image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.medianBlur(gray, 3)
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
 
  

   
    text = pytesseract.image_to_string(binary, lang="eng")

    return text



def process_pdf_from_memory_multiple(file_storages, text, image_storages , pytesseract ):
    global dbs
    dbs.clear()  # Clear previous DBs

    # Process PDFs
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
            extracted = extract_text_scanned_doc_from_stream(pdf_stream , pytesseract)
            # Add page number to metadata for each chunk
            page_chunks = []
            for page_num, text_on_page in extracted.items():
                chunks = text_splitter.split_text(text_on_page)
                page_chunks.extend([
                    Document(
                        page_content=chunk,
                        metadata={
                            "source": file_storage.filename,
                            "type": "pdf_scanned",
                            "page": page_num
                        }
                    ) for chunk in chunks
                ])
            all_docs.extend(page_chunks)
        else:
            print(f"Processing {file_storage.filename} as typed PDF...")
            doc = fitz.open(stream=pdf_stream, filetype="pdf")  # reload it
            for page_num, page in enumerate(doc):
                page_text = page.get_text()
                chunks = text_splitter.split_text(page_text)
                all_docs.extend([
                    Document(
                        page_content=chunk,
                        metadata={
                            "source": file_storage.filename,
                            "type": "pdf_typed",
                            "page": page_num + 1  # 1-based page number
                        }
                    ) for chunk in chunks
                ])
        dbs.append(FAISS.from_documents(documents=all_docs, embedding=embeddings))

    # Process extra text
    if text != "":
        data = text_splitter.split_text(text)
        docs_text = [
            Document(
                page_content=chunk,
                metadata={
                    "source": "user_text",
                    "type": "text"
                }
            ) for chunk in data
        ]
        dbs.append(FAISS.from_documents(documents=docs_text, embedding=embeddings))

    # Process images
    for image_storage in image_storages:
        image_stream = io.BytesIO(image_storage.read())
        extracted_text = extract_text_from_image_stream(image_stream , pytesseract)
        if extracted_text:
            data = text_splitter.split_text(extracted_text)
            docs = [
                Document(
                    page_content=chunk,
                    metadata={
                        "source": image_storage.filename,
                        "type": "image"
                    }
                ) for chunk in data
            ]
            dbs.append(FAISS.from_documents(documents=docs, embedding=embeddings))
