import React, { useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";

const API_URL = "/api";

export default function App() {
  const [sessionId, setSessionId] = useState("");
  const [sessions, setSessions] = useState([]);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [pending, setPending] = useState(false);
  const [error, setError] = useState("");
  const [sidebarOpen, setSidebarOpen] = useState(false);

  useEffect(() => {
    initializeChat();
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

  async function initializeChat() {
    setPending(true);
    try {
      const savedSessions = await requestJson("/sessions");
      setSessions(savedSessions);
      if (savedSessions.length > 0) {
        await openSession(savedSessions[0].session_id);
      } else {
        setSessionId(await createSession());
      }
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setPending(false);
    }
  }

  async function startNewChat() {
    setPending(true);
    setError("");
    try {
      const newSessionId = await createSession();
      setSessionId(newSessionId);
      setMessages([]);
      setInput("");
      setSidebarOpen(false);
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setPending(false);
    }
  }

  async function openSession(id) {
    setPending(true);
    setError("");
    try {
      const session = await requestJson(`/sessions/${id}`);
      setSessionId(session.session_id);
      setMessages(session.messages);
      setInput("");
      setSidebarOpen(false);
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
      setSessions((current) => {
        const previous = current.find((session) => session.session_id === sessionId);
        const title = previous?.title && previous.title !== "New chat"
          ? previous.title
          : message.length > 57
            ? `${message.slice(0, 57).trimEnd()}...`
            : message;
        return [
          {
            session_id: sessionId,
            title,
            updated_at: new Date().toISOString(),
          },
          ...current.filter((session) => session.session_id !== sessionId),
        ];
      });
    } catch (requestError) {
      setMessages((current) => current.slice(0, -1));
      setInput(message);
      setError(requestError.message);
    } finally {
      setPending(false);
    }
  }

  return (
    <div className="app-shell">
      <aside className={`sidebar ${sidebarOpen ? "sidebar-open" : ""}`}>
        <a className="brand" href="/" aria-label="Gen AI Chat home">
          <span className="brand-mark" aria-hidden="true">✳</span>
          <span>Gen AI</span>
        </a>
        <button
          className="new-chat"
          type="button"
          onClick={startNewChat}
          disabled={pending}
        >
          <span aria-hidden="true">+</span> New chat
        </button>
        <h2 className="history-heading">Chat history</h2>
        <nav className="history-list" aria-label="Chat history">
          {sessions.length === 0 ? (
            <p className="history-empty">Your conversations will show up here.</p>
          ) : (
            sessions.map((session) => (
              <button
                className={`history-item ${session.session_id === sessionId ? "active" : ""}`}
                type="button"
                key={session.session_id}
                onClick={() => openSession(session.session_id)}
                disabled={pending}
                aria-current={session.session_id === sessionId ? "page" : undefined}
                title={session.title}
              >
                {session.title}
              </button>
            ))
          )}
        </nav>
        <p className="sidebar-footer">Chats are saved on this MongoDB instance.</p>
      </aside>

      <main className="chat">
        <header>
          <button
            className="menu-toggle"
            type="button"
            aria-label={sidebarOpen ? "Close chat history" : "Open chat history"}
            onClick={() => setSidebarOpen((open) => !open)}
          >
            ☰
          </button>
          <div className="header-actions">
            <span
              className={`connection ${sessionId ? "connected" : ""}`}
              role="status"
            >
              <span className="connection-dot" />
              {sessionId ? "Ready" : pending ? "Connecting" : "Offline"}
            </span>
          </div>
        </header>

        <section className="conversation" aria-live="polite" aria-busy={pending}>
          {messages.length === 0 && (
            <div className="welcome">
              <span className="welcome-mark" aria-hidden="true">✳</span>
              <h1>How can I help?</h1>
              <p>Ask a question to get started.</p>
              {!sessionId && pending && <p className="status">Connecting to your chat...</p>}
            </div>
          )}
          {messages.map((item, index) => (
            <article className={`message ${item.role}`} key={`${index}-${item.role}`}>
              {item.role === "assistant" && (
                <span className="message-avatar" aria-label="Assistant">
                  ✳
                </span>
              )}
              <div className="message-body">
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
                <button type="button" onClick={initializeChat} disabled={pending}>
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
            onKeyDown={(event) => {
              if (event.key === "Enter" && !event.shiftKey) {
                event.preventDefault();
                event.currentTarget.form?.requestSubmit();
              }
            }}
            placeholder={sessionId ? "Message Gen AI..." : "Start the Python backend to chat"}
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
    </div>
  );
}
