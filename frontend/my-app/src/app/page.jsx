"use client";

import { useState, useEffect, useRef } from "react";
import { io } from "socket.io-client";

export default function Page() {
  const [pdfs, setPdfs] = useState([]);
  const [images, setImages] = useState([]);
  const [query, setQuery] = useState("");
  const [response, setResponse] = useState("");
  const [sources, setSources] = useState([]);
  const [loading, setLoading] = useState(false);
  const [extraText, setExtraText] = useState("");
  const [activeFile, setActiveFile] = useState(null);
  const [pdfPage, setPdfPage] = useState(0);
  const socketRef = useRef(null);

  useEffect(() => {
    socketRef.current = io("http://127.0.0.1:5000");
    socketRef.current.on("chat_response", (data) => {
      setResponse(data.response || "No answer available.");
      setSources(data.sources || []);
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

  const allFiles = [
    ...pdfs.map((f) => ({ file: f, type: "pdf" })),
    ...images.map((f) => ({ file: f, type: "image" })),
  ];

  return (
    <div className="flex h-screen">
      {/* Sidebar */}
      {allFiles ? (
        <aside className="w-44 bg-gray-100 p-4 border-r overflow-y-auto text-black">
          <h2 className="text-lg font-semibold mb-4">Uploaded Files</h2>
          <ul className="space-y-2">
            {allFiles.map(({ file, type }, idx) => (
              <li
                key={idx}
                onClick={() => setActiveFile({ file, type })}
                className={`text-sm cursor-pointer px-3 py-2 rounded  ${
                  activeFile?.file.name === file.name ? "bg-gray-300" : ""
                }`}>
                {type.toUpperCase()}: {file.name}
              </li>
            ))}
          </ul>
        </aside>
      ) : (
        <></>
      )}

      {/* Main content */}
      <main className="flex-1 flex flex-col overflow-hidden">
        <div className="flex flex-1 overflow-hidden">
          {/* File preview */}
          <div className="w-1/2 p-4 overflow-auto border-r">
            {activeFile ? (
              activeFile.type === "pdf" ? (
                <embed
                  src={`${URL.createObjectURL(
                    activeFile.file
                  )}#page=${pdfPage}`}
                  type="application/pdf"
                  className="w-full h-full"
                />
              ) : (
                <img
                  src={URL.createObjectURL(activeFile.file)}
                  alt="Preview"
                  className="w-full h-auto rounded shadow"
                />
              )
            ) : (
              <p className="text-gray-500">Select a file to preview</p>
            )}
          </div>

          {/* Chat and upload */}
          <div className="w-1/2 p-4 overflow-auto">
            <section className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Upload PDF(s), Image(s), and/or Enter Text
              </label>
              <div className="flex items-center gap-4 mb-4">
                <input
                  type="file"
                  accept="application/pdf"
                  multiple
                  onChange={(e) => setPdfs(Array.from(e.target.files))}
                  className="block text-sm text-gray-900 file:py-1 file:px-3 file:rounded-md file:border-0 file:bg-blue-100 file:text-blue-700 hover:file:bg-blue-200"
                />
                <input
                  type="file"
                  accept="image/*"
                  multiple
                  onChange={(e) => setImages(Array.from(e.target.files))}
                  className="block text-sm text-gray-900 file:py-1 file:px-3 file:rounded-md file:border-0 file:bg-green-100 file:text-green-700 hover:file:bg-green-200"
                />
              </div>
              <div className="flex flex-row ">
                <textarea
                  rows={1}
                  className="w-full border rounded-md p-2 resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Or type/paste a paragraph to upload with your files..."
                  value={extraText}
                  onChange={(e) => setExtraText(e.target.value)}
                  disabled={loading}
                />
                <button
                  onClick={handleUpload}
                  disabled={
                    loading ||
                    (!pdfs.length && !images.length && !extraText.trim())
                  }
                  className="px-5 h-fit py-2 my-2 mx-2 bg-blue-600 text-white rounded disabled:opacity-50">
                  Upload
                </button>
              </div>
            </section>

          {response && (
  <section className="bg-white rounded-lg p-6 shadow-md whitespace-pre-wrap">
    <strong className="block mb-4 text-xl font-semibold text-gray-800">Response:</strong>
    <p className="text-gray-700 mb-6">{response}</p>
    {sources.length > 0 && (
      <div className="mt-4">
        <strong className="block mb-3 text-lg font-medium text-gray-800">
          Individual document answers (tabular):
        </strong>
        <table className="min-w-full mb-6 border border-gray-200 rounded-lg overflow-hidden">
          <thead className="bg-blue-600 text-white">
            <tr>
              <th className="border border-gray-200 px-4 py-2 text-left text-sm font-semibold">Document ID</th>
              <th className="border border-gray-200 px-4 py-2 text-left text-sm font-semibold">Citation</th>
            </tr>
          </thead>
          <tbody>
            {sources.map((src, idx) => (
              <tr
                key={idx}
                className={`${idx % 2 === 0 ? 'bg-gray-50' : 'bg-white'} hover:bg-blue-50 transition-colors`}
              >
                <td className="border border-gray-200 px-4 py-2 text-gray-700">
                  {src.source
                    ? src.source
                    : "N/A"}
                </td>
             
                <td
                  className="border border-gray-200 px-4 py-2 text-blue-600 hover:underline cursor-pointer"
                  onClick={() => {
                    if (src.type === "pdf_scanned" || src.type === "pdf_typed") {
                      setPdfPage(parseInt(src["page"]));
                      for (let f of allFiles) {
                        if (f.file["name"] === src.source) {
                          setActiveFile({
                            file: f.file,
                            type: "pdf",
                          });
                        }
                      }
                    }
                  }}
                >
                  {src.type === "pdf_scanned" || src.type === "pdf_typed"
                    ? `Page ${src.page || "?"}`
                    : src.type === "image"
                    ? `Image: ${src.source}`
                    : src.type === "text"
                    ? "User Text"
                    : src.source}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        <strong className="block mb-3 text-lg font-medium text-gray-800">
          Synthesized (theme) answer (chat format):
        </strong>
        <div className="mt-2 p-4 bg-blue-100 rounded-lg shadow-sm text-gray-800">
          {response}
        </div>
      </div>
    )}
  </section>
)}

            <section className="my-6 flex flex-row ">
             
              <textarea
                rows={1}
                className="w-full border rounded-md p-2 resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Type your question here..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                disabled={loading}
              />
              <button
                onClick={handleAsk}
                disabled={loading || !query.trim()}
                className="ml-2 self-center h-fit px-6 py-2 bg-green-600 text-white rounded disabled:opacity-50">
                Ask
              </button>
            </section>
          </div>
        </div>
      </main>
    </div>
  );
}
