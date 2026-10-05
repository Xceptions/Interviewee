import React, { useState, useEffect, useRef } from "react";

interface Resume {
  filename: string;
  candidate_id: string;
}

interface Message {
  id: string;
  sender: "user" | "agent";
  text: string;
}

export default function App() {
  const [resumes, setResumes] = useState<Resume[]>([]);
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState("");
  const [threadId, setThreadId] = useState("");
  const [stage, setStage] = useState("inactive");
  const [isUploading, setIsUploading] = useState(false);
  const [isLoadingChat, setIsLoadingChat] = useState(false);
  
  const chatEndRef = useRef<HTMLDivElement>(null);
  const API_BASE = "http://127.0.0.1:8000";

  useEffect(() => {
    fetchResumes();
  }, []);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const fetchResumes = async () => {
    try {
      const res = await fetch(`${API_BASE}/resumes`);
      if (res.ok) {
        const data = await res.json();
        setResumes(data);
      }
    } catch (err) {
      console.error("Error fetching resumes:", err);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || e.target.files.length === 0) return;
    const file = e.target.files[0];
    const formData = new FormData();
    formData.append("file", file);

    setIsUploading(true);
    try {
      const res = await fetch(`${API_BASE}/resumes/upload`, {
        method: "POST",
        body: formData,
      });
      if (res.ok) {
        await fetchResumes();
        alert("Resume uploaded and ingested successfully!");
      } else {
        alert("Upload failed.");
      }
    } catch (err) {
      console.error(err);
    } finally {
      setIsUploading(false);
    }
  };

  const startNewInterview = async () => {
    const newThreadId = `session_${Date.now()}`;
    setThreadId(newThreadId);
    setIsLoadingChat(true);

    try {
      const res = await fetch(`${API_BASE}/interview/start?thread_id=${newThreadId}`, {
        method: "POST",
      });
      if (res.ok) {
        const data = await res.json();
        setStage(data.stage);
        setMessages([{ id: "init", sender: "agent", text: data.message }]);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoadingChat(false);
    }
  };

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputValue.trim() || !threadId || stage === "goodbye") return;

    const userText = inputValue;
    setInputValue("");
    
    const userMsgId = `user_${Date.now()}`;
    setMessages((prev) => [...prev, { id: userMsgId, sender: "user", text: userText }]);
    setIsLoadingChat(true);

    try {
      const res = await fetch(`${API_BASE}/interview/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ thread_id: threadId, message: userText }),
      });

      if (res.ok) {
        const data = await res.json();
        setStage(data.stage);
        setMessages((prev) => [
          ...prev,
          { id: `agent_${Date.now()}`, sender: "agent", text: data.message },
        ]);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoadingChat(false);
    }
  };

  return (
    <div style={{ display: "flex", height: "100vh", fontFamily: "sans-serif", backgroundColor: "#f3f4f6" }}>
      {/* Sidebar Layout */}
      <div style={{ width: "320px", borderRight: "1px solid #e5e7eb", backgroundColor: "#ffffff", padding: "20px", display: "flex", flexDirection: "column" }}>
        <h2 style={{ fontSize: "1.25rem", fontWeight: "bold", marginBottom: "20px", color: "#1f2937" }}>Resumes</h2>
        
        {/* Upload Interface */}
        <label style={{ display: "block", padding: "10px", backgroundColor: "#3b82f6", color: "#ffffff", textAlign: "center", borderRadius: "6px", cursor: "pointer", fontWeight: "6px", marginBottom: "20px" }}>
          {isUploading ? "Uploading..." : "Upload Resume"}
          <input type="file" accept=".pdf,.docx" onChange={handleFileUpload} disabled={isUploading} style={{ display: "none" }} />
        </label>

        {/* Dynamic File Item List */}
        <div style={{ flex: 1, overflowY: "auto" }}>
          {resumes.length === 0 ? (
            <p style={{ color: "#9ca3af", fontSize: "0.875rem" }}>No resumes uploaded yet.</p>
          ) : (
            resumes.map((resume, idx) => (
              <div key={idx} style={{ padding: "10px", backgroundColor: "#f9fafb", border: "1px solid #e5e7eb", borderRadius: "6px", marginBottom: "8px", fontSize: "0.875rem", color: "#4b5563", wordBreak: "break-all" }}>
                📄 {resume.filename}
              </div>
            ))
          )}
        </div>
      </div>

      {/* Primary Workspace Chat Engine */}
      <div style={{ flex: 1, display: "flex", flexDirection: "column", backgroundColor: "#f3f4f6" }}>
        {/* Workspace Top Header Bar */}
        <div style={{ padding: "20px", backgroundColor: "#ffffff", borderBottom: "1px solid #e5e7eb", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <div>
            <h1 style={{ fontSize: "1.5rem", fontWeight: "bold", color: "#1f2937" }}>AI Interview Panel</h1>
            {stage !== "inactive" && <span style={{ fontSize: "0.75rem", textTransform: "uppercase", padding: "2px 8px", backgroundColor: "#e0f2fe", color: "#0369a1", borderRadius: "9999px", fontWeight: "bold" }}>Stage: {stage}</span>}
          </div>
          {stage === "inactive" || stage === "goodbye" ? (
            <button onClick={startNewInterview} style={{ padding: "10px 20px", backgroundColor: "#10b981", color: "#ffffff", border: "none", borderRadius: "6px", fontWeight: "bold", cursor: "pointer" }}>
              Start Interview Process
            </button>
          ) : null}
        </div>

        {/* Screen Feed Panels */}
        <div style={{ flex: 1, padding: "20px", overflowY: "auto", display: "flex", flexDirection: "column", gap: "15px" }}>
          {messages.length === 0 ? (
            <div style={{ display: "flex", justifyContent: "center", alignItems: "center", height: "100%", color: "#9ca3af" }}>
              Click "Start Interview Process" to spin up the agent workflow loop.
            </div>
          ) : (
            messages.map((msg) => (
              <div key={msg.id} style={{ display: "flex", justifyContent: msg.sender === "user" ? "flex-end" : "flex-start" }}>
                <div style={{ maxWidth: "70%", padding: "12px 16px", borderRadius: "12px", fontSize: "0.95rem", lineHeight: "1.5", backgroundColor: msg.sender === "user" ? "#3b82f6" : "#ffffff", color: msg.sender === "user" ? "#ffffff" : "#1f2937", border: msg.sender === "user" ? "none" : "1px solid #e5e7eb", boxShadow: "0 1px 2px 0 rgba(0, 0, 0, 0.05)" }}>
                  {msg.text}
                </div>
              </div>
            ))
          )}
          {isLoadingChat && (
            <div style={{ display: "flex", justifyContent: "flex-start" }}>
              <div style={{ padding: "12px 16px", color: "#9ca3af", fontStyle: "italic", fontSize: "0.875rem" }}>
                Helen Reece is thinking...
              </div>
            </div>
          )}
          <div ref={chatEndRef} />
        </div>

        {/* Input Interface Form Controls */}
        <form onSubmit={handleSendMessage} style={{ padding: "20px", backgroundColor: "#ffffff", borderTop: "1px solid #e5e7eb", display: "flex", gap: "10px" }}>
          <input type="text" value={inputValue} onChange={(e) => setInputValue(e.target.value)} disabled={stage === "inactive" || stage === "goodbye" || isLoadingChat} placeholder={stage === "goodbye" ? "The interview has concluded." : "Type your answer here..."} style={{ flex: 1, padding: "12px", border: "1px solid #d1d5db", borderRadius: "6px", fontSize: "1  rem", outline: "none" }} />
          <button type="submit" disabled={stage === "inactive" || stage === "goodbye" || !inputValue.trim() || isLoadingChat} style={{ padding: "12px 24px", backgroundColor: stage === "goodbye" || stage === "inactive" ? "#d1d5db" : "#3b82f6", color: "#ffffff", border: "none", borderRadius: "6px", fontWeight: "bold", cursor: "pointer" }}>
            Send
          </button>
        </form>
      </div>
    </div>
  );
}
