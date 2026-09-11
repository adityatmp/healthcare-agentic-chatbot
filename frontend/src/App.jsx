import { useState } from "react";
import ReactMarkdown from "react-markdown";
import "./App.css";

const API_BASE_URL = "http://127.0.0.1:8000";

function App() {
  const [messages, setMessages] = useState([]);
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);

  const suggestedQuestions = [
    "What lifestyle changes can help with high blood pressure?",
    "What is the DASH diet?",
    "How much sodium is recommended for high blood pressure?",
  ];

  async function sendMessage(text = question) {
    const trimmed = text.trim();

    if (!trimmed || loading) return;

    const userMessage = {
      id: crypto.randomUUID(),
      role: "user",
      content: trimmed,
    };

    setMessages((current) => [...current, userMessage]);
    setQuestion("");
    setLoading(true);

    try {
      const response = await fetch(`${API_BASE_URL}/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          question: trimmed,
        }),
      });

      if (!response.ok) {
        throw new Error(`Request failed with HTTP ${response.status}`);
      }

      const data = await response.json();

      setMessages((current) => [
        ...current,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          content:
            data.answer ||
            "I couldn't generate a response. Please try again.",
          grounded: data.grounded,
          abstained: data.abstained,
          sources: data.sources || [],
          tool_used: data.tool_used || null,
        },
      ]);
    } catch (error) {
      console.error(error);

      setMessages((current) => [
        ...current,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          error: true,
          content:
            "I couldn't connect to the healthcare assistant. Make sure the FastAPI backend is running.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  function handleSubmit(event) {
    event.preventDefault();
    sendMessage();
  }

  function handleKeyDown(event) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      sendMessage();
    }
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand">
          <div className="brand-mark">+</div>

          <div>
            <div className="brand-name">HealthRAG</div>
            <div className="brand-subtitle">
              Grounded healthcare information assistant
            </div>
          </div>
        </div>

        <div className="status-pill">
          <span className="status-dot" />
          Local AI
        </div>
      </header>

      <main className="main-content">
        {messages.length === 0 ? (
          <section className="welcome-section">
            <div className="hero-icon">✚</div>

            <p className="eyebrow">PRIVATE • GROUNDED • LOCAL</p>

            <h1>
              Ask about your
              <span> health information.</span>
            </h1>

            <p className="hero-description">
              Get answers grounded in the healthcare documents available to
              this assistant, with source and page citations when available.
            </p>

            <div className="suggestion-grid">
              {suggestedQuestions.map((item) => (
                <button
                  className="suggestion-card"
                  key={item}
                  onClick={() => sendMessage(item)}
                >
                  <span>{item}</span>
                  <span className="arrow">↗</span>
                </button>
              ))}
            </div>
          </section>
        ) : (
          <section className="chat-section">
            {messages.map((message) => (
              <article
                key={message.id}
                className={`message-row ${message.role === "user"
                  ? "user-row"
                  : "assistant-row"
                  }`}
              >
                <div
                  className={`message-bubble ${message.role === "user"
                    ? "user-bubble"
                    : "assistant-bubble"
                    } ${message.error ? "error-bubble" : ""}`}
                >
                  <div className="message-label">
                    {message.role === "user" ? "You" : "HealthRAG"}
                  </div>

                  <div className="message-content">
                    {message.role === "assistant" && !message.error ? (
                      <ReactMarkdown>{message.content}</ReactMarkdown>
                    ) : (
                      message.content
                    )}
                  </div>

                  {message.role === "assistant" && !message.error && (
                    <div className="response-meta">
                      <div className="response-badges">
                        {message.grounded && (
                          <span className="badge grounded-badge">
                            ✓ Grounded
                          </span>
                        )}

                        {message.abstained && (
                          <span className="badge abstained-badge">
                            Evidence insufficient
                          </span>
                        )}

                        {message.tool_used && !message.abstained && (
                          <span className="badge tool-badge">
                            Reference tool used
                          </span>
                        )}
                      </div>

                      {message.sources.length > 0 && (
                        <div className="sources">
                          <div className="sources-title">Sources</div>

                          {message.sources.map((source, index) => (
                            <div
                              className="source-item"
                              key={`${source.document}-${source.page}-${index}`}
                            >
                              <span className="source-number">
                                {index + 1}
                              </span>

                              <div className="source-details">
                                <div className="source-document">
                                  {source.title || source.document}
                                </div>

                                <div className="source-page">
                                  Page {source.page}
                                  {source.organization && (
                                    <span className="source-org">
                                      {" "}• {source.organization}
                                    </span>
                                  )}
                                </div>

                                {source.url && (
                                  <a
                                    className="source-link"
                                    href={source.url}
                                    target="_blank"
                                    rel="noreferrer"
                                  >
                                    Official Reference ↗
                                  </a>
                                )}
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </article>
            ))}

            {loading && (
              <article className="message-row assistant-row">
                <div className="message-bubble assistant-bubble">
                  <div className="message-label">HealthRAG</div>

                  <div className="typing-indicator">
                    <span />
                    <span />
                    <span />
                    <em>Searching healthcare sources…</em>
                  </div>
                </div>
              </article>
            )}
          </section>
        )}

        <section className="composer-section">
          <form className="composer" onSubmit={handleSubmit}>
            <textarea
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask a healthcare question..."
              rows={1}
              disabled={loading}
            />

            <button
              className="send-button"
              type="submit"
              disabled={!question.trim() || loading}
            >
              ↑
            </button>
          </form>

          <div className="composer-note">
            Answers are grounded in the available healthcare sources.
          </div>
        </section>
      </main>

      <footer className="footer">
        <div>HealthRAG • Local healthcare knowledge assistant</div>

        <div className="footer-disclaimer">
          Not a doctor. Not a substitute for professional medical advice.
        </div>
      </footer>
    </div>
  );
}

export default App;