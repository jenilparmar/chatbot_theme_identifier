"use client";

import { useState, useEffect, useRef } from "react";
import { io } from "socket.io-client";

export default function Page() {
  const [pdfs, setPdfs] = useState([]);
  const [images, setImages] = useState([]); // New state for images
  const [query, setQuery] = useState("");
  const [response, setResponse] = useState("");
  const [sources, setSources] = useState([]); // <-- NEW
  const [loading, setLoading] = useState(false);
  const [extraText, setExtraText] = useState(""); // New state for extra text
  const socketRef = useRef(null);

  useEffect(() => {
    socketRef.current = io("http://127.0.0.1:5000");
    socketRef.current.on("chat_response", (data) => {
      setResponse(data.response || "No answer available.");
      setSources(data.sources || []); // <-- NEW
      // Optionally update chat history here
    });
    return () => {
      socketRef.current.disconnect();
    };
  }, []);

  const handleUpload = async () => {
    if (!pdfs.length && !images.length && !extraText.trim()) {
      alert(
        "Please select at least one PDF, image, or enter some text to upload."
      );
      return;
    }
    const formData = new FormData();
    for (let i = 0; i < pdfs.length; i++) {
      formData.append("pdf", pdfs[i]);
    }
    for (let i = 0; i < images.length; i++) {
      formData.append("image", images[i]);
    }
    if (extraText.trim()) {
      formData.append("text", extraText);
    }

    setLoading(true);
    setResponse("Uploading files and text...");
    try {
      const res = await fetch("http://127.0.0.1:5000/upload", {
        method: "POST",
        body: formData,
      });
      const data = await res.json();
      setResponse(data.message || "Files and text uploaded successfully.");
    } catch (err) {
      setResponse("Upload failed.");
    }
    setLoading(false);
  };

  const handleAsk = () => {
    if (!query.trim()) return;
    setLoading(true);
    setResponse("Generating answer...");
    socketRef.current.emit("chat_message", { query });
    setLoading(false);
  };

  return (
    <main className="max-w-2xl mx-auto py-10 px-4">
      <h1 className="text-3xl font-bold mb-8 text-center">
        PDF Q&A with Gemini
      </h1>

      <section className="mb-8">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Upload PDF(s), Image(s), and/or Enter Text
        </label>
        <div className="flex items-center gap-4 mb-4">
          <input
            type="file"
            accept="application/pdf"
            multiple
            onChange={(e) => setPdfs(Array.from(e.target.files))}
            className="block w-full text-sm text-gray-900
              file:mr-4 file:py-2 file:px-4
              file:rounded-md file:border-0
              file:text-sm file:font-semibold
              file:bg-blue-100 file:text-blue-700
              hover:file:bg-blue-200"
          />
          <input
            type="file"
            accept="image/*"
            multiple
            onChange={(e) => setImages(Array.from(e.target.files))}
            className="block w-full text-sm text-gray-900
              file:mr-4 file:py-2 file:px-4
              file:rounded-md file:border-0
              file:text-sm file:font-semibold
              file:bg-green-100 file:text-green-700
              hover:file:bg-green-200"
          />
          <button
            onClick={handleUpload}
            disabled={
              loading || (!pdfs.length && !images.length && !extraText.trim())
            }
            className="px-5 py-2 bg-blue-600 text-white rounded disabled:opacity-50">
            Upload
          </button>
        </div>
        <textarea
          rows={4}
          className="w-full border rounded-md p-3 resize-none mb-2
            focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="Or type/paste a paragraph to upload with your files..."
          value={extraText}
          onChange={(e) => setExtraText(e.target.value)}
          disabled={loading}
        />
      </section>

      <section className="mb-8">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Ask a question about the PDF
        </label>
        <textarea
          rows={5}
          className="w-full border rounded-md p-3 resize-none
            focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="Type your question here..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          disabled={loading}
        />
        <button
          onClick={handleAsk}
          disabled={loading || !query.trim()}
          className="mt-3 px-6 py-2 bg-green-600 text-white rounded disabled:opacity-50">
          Ask
        </button>
      </section>

      {response && (
        <section className="border rounded-md p-4 bg-black whitespace-pre-wrap">
          <strong className="block mb-2 text-white">Response:</strong>
          <p>{response}</p>
          {sources.length > 0 && (
            <div className="mt-4">
              <strong className="text-white">Sources:</strong>
              <ul className="list-disc ml-6 text-gray-300">
                {sources.map((src, idx) => (
                  <li key={idx}>
                    {src.type === "pdf_scanned" || src.type === "pdf_typed"
                      ? `PDF: ${src.source} , Page no: ${src['page']}`
                      : src.type === "image"
                      ? `Image: ${src.source}`
                      : src.type === "text"
                      ? "User Text"
                      : src.source}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </section>
      )}
    </main>
  );
}
