"use client";

import { useState } from "react";

export default function Page() {
  const [pdf, setPdf] = useState(null);
  const [query, setQuery] = useState("");
  const [response, setResponse] = useState("");
  const [loading, setLoading] = useState(false);

  const handleUpload = async () => {
    if (!pdf) {
      alert("Please select a PDF to upload.");
      return;
    }
    const formData = new FormData();
    formData.append("pdf", pdf);

    setLoading(true);
    setResponse("Uploading PDF...");
    try {
      const res = await fetch("http://127.0.0.1:5000/upload", {
        method: "POST",
        body: formData,
      });
      const data = await res.json();
      setResponse(data.message || "PDF uploaded successfully.");
    } catch (err) {
      setResponse("Upload failed.");
    }
    setLoading(false);
  };

  const handleAsk = async () => {
    if (!query.trim()) return;
    setLoading(true);
    setResponse("Generating answer...");
    try {
      const res = await fetch("http://127.0.0.1:5000/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query }),
      });
      const data = await res.json();
      setResponse(data.response || "No answer available.");
    } catch (err) {
      setResponse("Failed to get response.");
    }
    setLoading(false);
  };

  return (
    <main className="max-w-2xl mx-auto py-10 px-4">
      <h1 className="text-3xl font-bold mb-8 text-center">PDF Q&A with Gemini</h1>

      <section className="mb-8">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Upload PDF
        </label>
        <div className="flex items-center gap-4">
          <input
            type="file"
            accept="application/pdf"
            onChange={(e) => setPdf(e.target.files?.[0] || null)}
            className="block w-full text-sm text-gray-900
              file:mr-4 file:py-2 file:px-4
              file:rounded-md file:border-0
              file:text-sm file:font-semibold
              file:bg-blue-100 file:text-blue-700
              hover:file:bg-blue-200"
          />
          <button
            onClick={handleUpload}
            disabled={!pdf || loading}
            className="px-5 py-2 bg-blue-600 text-white rounded disabled:opacity-50"
          >
            Upload
          </button>
        </div>
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
          className="mt-3 px-6 py-2 bg-green-600 text-white rounded disabled:opacity-50"
        >
          Ask
        </button>
      </section>

      {response && (
        <section className="border rounded-md p-4 bg-gray-100 whitespace-pre-wrap">
          <strong className="block mb-2 text-gray-800">Response:</strong>
          <p>{response}</p>
        </section>
      )}
    </main>
  );
}
