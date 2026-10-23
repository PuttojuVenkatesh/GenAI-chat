import { useState } from "react";
import ReactMarkdown from "react-markdown";

const API_URL = "http://127.0.0.1:8000/chat";

export default function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [pending, setPending] = useState(false);
  const [error, setError] = useState("");

  async function sendMessage(event) {
    event.preventDefault();
    const message = input.trim();
    if (!message || pending) return;

    const history = messages.map(({ role, content }) => ({ role, content }));
    setMessages((current) => [...current, { role: "user", content: message }]);
    setInput("");
    setError("");
    setPending(true);

    try {
      const response = await fetch(API_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message, history: history.slice(-8) }),
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || "The request failed.");
      }
      setMessages((current) => [
        ...current,
        { role: "assistant", content: data.reply, intent: data.intent },
      ]);
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setPending(false);
    }
  }

  return (
    <main className="chat">
      <header>
        <h1>Gen AI Chat</h1>
        <p>Ask a question or continue the conversation.</p>
      </header>

      <section className="conversation" aria-live="polite">
        {messages.length === 0 && (
          <p className="empty">Your conversation will appear here.</p>
        )}
        {messages.map((item, index) => (
          <article className={`message ${item.role}`} key={`${index}-${item.role}`}>
            <strong>{item.role === "user" ? "You" : "Assistant"}</strong>
            {item.intent && <small>Intent: {item.intent}</small>}
            {item.role === "assistant" ? (
              <div className="markdown">
                <ReactMarkdown>{item.content}</ReactMarkdown>
              </div>
            ) : (
              <p>{item.content}</p>
            )}
          </article>
        ))}
        {pending && <p className="status">Thinking…</p>}
        {error && <p className="error" role="alert">{error}</p>}
      </section>

      <form onSubmit={sendMessage}>
        <label className="sr-only" htmlFor="message">Your message</label>
        <textarea
          id="message"
          value={input}
          onChange={(event) => setInput(event.target.value)}
          placeholder="Type a message..."
          rows="3"
          disabled={pending}
        />
        <button type="submit" disabled={pending || !input.trim()}>
          Send
        </button>
      </form>
    </main>
  );
}
