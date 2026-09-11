import { useState, useEffect, useRef } from "react";
import ReactMarkdown from "react-markdown";
import "./App.css";

const API_BASE_URL = "http://127.0.0.1:8000";

const SUGGESTED_QUESTIONS = [
  "What helps lower blood pressure?",
  "What is the DASH diet?",
  "What is the upper limit for boron?",
];

function routeLabel(msg) {
  if (msg.abstained) return null;
  if (msg.tool_used && msg.grounded)
    return `MCP \u00b7 ${msg.sources?.length ?? 0} source${msg.sources?.length !== 1 ? "s" : ""}`;
  if (msg.tool_used) return "MCP \u00b7 Reference lookup";
  if (msg.grounded)
    return `RAG \u00b7 ${msg.sources?.length ?? 0} source${msg.sources?.length !== 1 ? "s" : ""}`;
  return null;
}

export default function App() {
  const [messages, setMessages] = useState([]);
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef(null);
  const textareaRef = useRef(null);
  // Synchronous in-flight guard — prevents double-submission caused by
  // Enter keydown firing sendMessage AND the form submit event both seeing
  // a stale loading=false before React batches the state update.
  const inFlightRef = useRef(false);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 160)}px`;
  }, [question]);

  async function sendMessage(text = question) {
    const trimmed = text.trim();
    // inFlightRef is updated synchronously (unlike React state) so concurrent
    // calls from both the keydown handler and the form submit event are blocked.
    if (!trimmed || inFlightRef.current) return;
    inFlightRef.current = true;
    setMessages((cur) => [
      ...cur,
      { id: crypto.randomUUID(), role: "user", content: trimmed },
    ]);
    setQuestion("");
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE_URL}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: trimmed }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setMessages((cur) => [
        ...cur,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          content: data.answer || "I could not generate a response. Please try again.",
          grounded: data.grounded ?? false,
          abstained: data.abstained ?? false,
          sources: data.sources ?? [],
          tool_used: data.tool_used ?? null,
        },
      ]);
    } catch (err) {
      console.error(err);
      setMessages((cur) => [
        ...cur,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          error: true,
          content:
            "Could not reach the healthcare assistant. Ensure the FastAPI backend is running on port 8000.",
        },
      ]);
    } finally {
      setLoading(false);
      inFlightRef.current = false;
    }
  }

  function handleSubmit(e) {
    e.preventDefault();
    sendMessage();
  }

  function handleKeyDown(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      // Prevent the keydown from also triggering the form's submit event,
      // which would call sendMessage a second time via handleSubmit.
      e.preventDefault();
      e.stopPropagation();
      sendMessage();
    }
  }

  const hasMessages = messages.length > 0;

  return (
    <div className="shell">
      <header className="site-header">
        <span className="wordmark">HealthRAG</span>
        <span className="header-meta">Local AI</span>
      </header>

      <div className="body">
        <div className="chat-region" aria-live="polite">
          {!hasMessages ? (
            <div className="empty-state">
              <p className="empty-heading">What can I help you find?</p>
              <p className="empty-sub">
                Ask a health-related question using the available sources.
              </p>
              <ul className="suggestion-list">
                {SUGGESTED_QUESTIONS.map((q) => (
                  <li key={q}>
                    <button
                      className="suggestion-btn"
                      type="button"
                      onClick={() => sendMessage(q)}
                    >
                      {q}
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          ) : (
            <div className="message-list">
              {messages.map((msg) => (
                <div
                  key={msg.id}
                  className={`message-row ${msg.role === "user" ? "user-row" : "assistant-row"}`}
                >
                  {msg.role === "user" ? (
                    <div className="user-bubble">{msg.content}</div>
                  ) : (
                    <div className={`assistant-block${msg.error ? " error-block" : ""}`}>
                      <div className="assistant-label">HealthRAG</div>
                      <div className="message-content">
                        {msg.error ? (
                          msg.content
                        ) : (
                          <ReactMarkdown>{msg.content}</ReactMarkdown>
                        )}
                      </div>

                      {!msg.error && routeLabel(msg) && (
                        <p className="route-meta">{routeLabel(msg)}</p>
                      )}

                      {!msg.error && msg.abstained && (
                        <p className="abstained-notice">
                          The available sources do not contain sufficient information to answer this question.
                        </p>
                      )}

                      {!msg.error && msg.sources && msg.sources.length > 0 && (
                        <div className="sources">
                          <div className="sources-divider" />
                          <p className="sources-heading">Source</p>
                          {msg.sources.map((src, i) => (
                            <div
                              className="source-entry"
                              key={`${src.document}-${src.page}-${i}`}
                            >
                              {src.organization && (
                                <span className="source-org">{src.organization}</span>
                              )}
                              <span className="source-title">
                                {src.title || src.document}
                              </span>
                              {src.page && (
                                <span className="source-page">Page {src.page}</span>
                              )}
                              {src.url && (
                                <a
                                  className="source-link"
                                  href={src.url}
                                  target="_blank"
                                  rel="noreferrer"
                                >
                                  official source
                                </a>
                              )}
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ))}

              {loading && (
                <div className="message-row assistant-row">
                  <div className="assistant-block">
                    <div className="assistant-label">HealthRAG</div>
                    <div className="thinking-dots">
                      <span /><span /><span />
                    </div>
                  </div>
                </div>
              )}

              <div ref={bottomRef} />
            </div>
          )}
        </div>

        <div className="composer-wrap">
          <form className="composer" onSubmit={handleSubmit}>
            <textarea
              ref={textareaRef}
              id="chat-input"
              className="composer-input"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask a healthcare question..."
              rows={1}
              disabled={loading}
              aria-label="Healthcare question input"
            />
            <button
              className="composer-send"
              type="submit"
              disabled={!question.trim() || loading}
              aria-label="Send"
            >
              Send
            </button>
          </form>
          <p className="composer-note">
            Grounded in curated healthcare sources. Not a substitute for professional medical advice.
          </p>
        </div>
      </div>
    </div>
  );
}
