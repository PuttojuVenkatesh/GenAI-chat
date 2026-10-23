import React from "react";
import { useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";

const API_URL = "/api";

export default function App() {
  const [sessionId, setSessionId] = useState("");
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [pending, setPending] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    startNewChat();
  }, []);

  async function requestJson(path, options) {
    let response;
    try {
      response = await fetch(`${API_URL}${path}`, options);
    } catch {
      throw new Error(
        "Cannot connect to the Python backend. Start it in Terminal 1, then select Retry.",
      );
    }

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || "The request failed.");
    }
    return data;
  }

  async function createSession() {
    const data = await requestJson("/sessions", { method: "POST" });
    return data.session_id;
  }

  async function startNewChat() {
    setPending(true);
    setError("");
    try {
      const newSessionId = await createSession();
      setSessionId(newSessionId);
      setMessages([]);
      setInput("");
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setPending(false);
    }
  }

  async function sendMessage(event) {
    event.preventDefault();
    const message = input.trim();
    if (!message || pending || !sessionId) return;

    setMessages((current) => [...current, { role: "user", content: message }]);
    setInput("");
    setError("");
    setPending(true);

    try {
      const data = await requestJson("/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId, message }),
      });
      setMessages((current) => [
        ...current,
        { role: "assistant", content: data.reply, intent: data.intent },
      ]);
    } catch (requestError) {
      setMessages((current) => current.slice(0, -1));
      setInput(message);
      setError(requestError.message);
    } finally {
      setPending(false);
    }
  }

  return (
    <main className="chat">
      <header>
        <a className="brand" href="/" aria-label="Gen AI Chat home">
          <span className="brand-mark" aria-hidden="true">G</span>
          <span>Gen AI <span className="brand-light">Chat</span></span>
        </a>
        <div className="header-actions">
          <span className={`connection ${sessionId ? "connected" : ""}`}>
            <span className="connection-dot" />
            {sessionId ? "Ready" : pending ? "Connecting" : "Offline"}
          </span>
          <button
            className="new-chat"
            type="button"
            onClick={startNewChat}
            disabled={pending}
          >
            <span aria-hidden="true">+</span> New chat
          </button>
        </div>
      </header>

      <section className="conversation" aria-live="polite" aria-busy={pending}>
        {messages.length === 0 && (
          <div className="welcome">
            <span className="welcome-mark" aria-hidden="true">✳</span>
            <h1>What can I help with?</h1>
            <p>Ask a question or start a conversation. Your chat stays separate when you choose New chat.</p>
            {!sessionId && pending && <p className="status">Connecting to your chat...</p>}
          </div>
        )}
        {messages.map((item, index) => (
          <article className={`message ${item.role}`} key={`${index}-${item.role}`}>
            <span className="message-avatar" aria-hidden="true">
              {item.role === "user" ? "Y" : "✳"}
            </span>
            <div className="message-body">
              <strong>{item.role === "user" ? "You" : "Assistant"}</strong>
              {item.intent && <small>Intent: {item.intent}</small>}
            {item.role === "assistant" ? (
              <div className="markdown">
                <ReactMarkdown>{item.content}</ReactMarkdown>
              </div>
            ) : (
              <p>{item.content}</p>
            )}
            </div>
          </article>
        ))}
        {pending && sessionId && <p className="status">Thinking…</p>}
        {error && (
          <div className="error" role="alert">
            <span>{error}</span>
            {!sessionId && (
              <button type="button" onClick={startNewChat} disabled={pending}>
                Retry
              </button>
            )}
          </div>
        )}
      </section>

      <form onSubmit={sendMessage}>
        <label className="sr-only" htmlFor="message">Your message</label>
        <textarea
          id="message"
          value={input}
          onChange={(event) => setInput(event.target.value)}
          placeholder={sessionId ? "Message Gen AI Chat..." : "Start the Python backend to chat"}
          rows="2"
          disabled={pending}
        />
        <button
          className="send-button"
          type="submit"
          aria-label="Send message"
          disabled={pending || !sessionId || !input.trim()}
        >
          <span aria-hidden="true">↑</span>
        </button>
      </form>
      <p className="footnote">AI responses can be inaccurate. Avoid sharing sensitive information.</p>
    </main>
  );
}
