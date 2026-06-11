import { useState, useRef, useEffect, useCallback } from "react";
import "./App.css";

const API_URL = "https://dag-chatbot-production.up.railway.app";

const MODES = [
  { id: "chat",     label: "Chat",     desc: "Ask anything" },
  { id: "devotion", label: "Devotion", desc: "Daily devotional guide" },
  { id: "sermon",   label: "Sermon",   desc: "Sermon outline" },
  { id: "study",    label: "Study",    desc: "Deep study notes" },
];

const SUGGESTIONS = [
  "What does Bishop Dag say about loyalty?",
  "How do I grow in the anointing?",
  "What are the signs of a disloyal person?",
  "How should a pastor handle betrayal?",
];

const WELCOME = "Hello. I'm Dag Bot — your guide to Bishop Dag Heward-Mills' teachings across 132 books. What would you like to explore today?";

function formatText(text) {
  const lines = text.split('\n');
  const elements = [];
  let key = 0;

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];

    if (/^---+$/.test(line.trim())) {
      elements.push(<hr key={key++} className="msg-divider" />);
      continue;
    }

    const headingMatch = line.match(/^#{1,3}\s+(.+)$/);
    if (headingMatch) {
      elements.push(
        <p key={key++} className="msg-heading">
          {renderInline(headingMatch[1])}
        </p>
      );
      continue;
    }

    const numberedHeading = line.match(/^(\d+)\.\s+\*\*(.+?)\*\*(.*)$/);
    if (numberedHeading) {
      elements.push(
        <p key={key++} className="msg-heading">
          {numberedHeading[1]}. {numberedHeading[2]}{numberedHeading[3]}
        </p>
      );
      continue;
    }

    if (!line.trim()) {
      elements.push(<div key={key++} className="msg-gap" />);
      continue;
    }

    elements.push(
      <span key={key++} className="msg-line">
        {renderInline(line)}
        <br />
      </span>
    );
  }

  return elements;
}

function renderInline(text) {
  const parts = text.split(/\*\*(.*?)\*\*/g);
  return parts.map((part, i) =>
    i % 2 === 1 ? <strong key={i}>{part}</strong> : part
  );
}

function SourcesButton({ sources }) {
  const [open, setOpen] = useState(false);
  if (!sources || sources.length === 0) return null;

  return (
    <div className="sources-wrap">
      <button className="sources-btn" onClick={() => setOpen(o => !o)}>
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/>
          <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/>
        </svg>
        Sources ({sources.length})
        <svg
          width="10" height="10" viewBox="0 0 24 24"
          fill="none" stroke="currentColor" strokeWidth="2.5"
          style={{ transform: open ? "rotate(180deg)" : "rotate(0deg)", transition: "transform 0.2s" }}
        >
          <polyline points="6 9 12 15 18 9"/>
        </svg>
      </button>

      {open && (
        <div className="sources-panel">
          {sources.map((s, i) => (
            <div key={i} className="source-card">
              <div className="source-book">{s.book}</div>
              {s.chapter && <div className="source-chapter">{s.chapter}</div>}
              <div className="source-excerpt">"{s.excerpt}"</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function MessageActions({ content, onRetry }) {
  const [copied, setCopied]   = useState(false);
  const [liked, setLiked]     = useState(false);
  const [disliked, setDisliked] = useState(false);

  const copy = () => {
    navigator.clipboard.writeText(content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const like = () => { setLiked(o => !o); setDisliked(false); };
  const dislike = () => { setDisliked(o => !o); setLiked(false); };

  return (
    <div className="msg-actions">
      <button className={`action-btn ${copied ? "active" : ""}`} onClick={copy} title="Copy">
        {copied ? (
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
            <polyline points="20 6 9 17 4 12"/>
          </svg>
        ) : (
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
          </svg>
        )}
      </button>

      <button className={`action-btn ${liked ? "active" : ""}`} onClick={like} title="Good response">
        <svg width="13" height="13" viewBox="0 0 24 24" fill={liked ? "currentColor" : "none"} stroke="currentColor" strokeWidth="2">
          <path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3H14z"/>
          <path d="M7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3"/>
        </svg>
      </button>

      <button className={`action-btn ${disliked ? "active" : ""}`} onClick={dislike} title="Poor response">
        <svg width="13" height="13" viewBox="0 0 24 24" fill={disliked ? "currentColor" : "none"} stroke="currentColor" strokeWidth="2">
          <path d="M10 15v4a3 3 0 0 0 3 3l4-9V2H5.72a2 2 0 0 0-2 1.7l-1.38 9a2 2 0 0 0 2 2.3H10z"/>
          <path d="M17 2h2.67A2.31 2.31 0 0 1 22 4v7a2.31 2.31 0 0 1-2.33 2H17"/>
        </svg>
      </button>

      <button className="action-btn" onClick={onRetry} title="Regenerate response">
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <polyline points="1 4 1 10 7 10"/>
          <path d="M3.51 15a9 9 0 1 0 .49-3.5"/>
        </svg>
      </button>
    </div>
  );
}

function UserMessage({ content, onEdit }) {
  const [hovered, setHovered] = useState(false);
  const [copied, setCopied] = useState(false);

  const copy = () => {
    navigator.clipboard.writeText(content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div
      className="user-msg-wrap"
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
    >
      {hovered && (
        <div className="user-actions">
          <button className="action-btn" onClick={() => onEdit(content)} title="Edit">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
              <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
            </svg>
          </button>
          <button className={`action-btn ${copied ? "active" : ""}`} onClick={copy} title="Copy">
            {copied ? (
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <polyline points="20 6 9 17 4 12"/>
              </svg>
            ) : (
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <rect x="9" y="9" width="13" height="13" rx="2"/>
                <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
              </svg>
            )}
          </button>
        </div>
      )}
      <div className="user-bubble">{content}</div>
    </div>
  );
}

export default function App() {
  const [chats, setChats] = useState([
    { id: 1, title: "New Chat", messages: [{ role: "assistant", content: WELCOME, sources: [], isWelcome: true }] }
  ]);
  const [activeChatId, setActiveChatId] = useState(1);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [mode, setMode] = useState("chat");
  const [modeMenuOpen, setModeMenuOpen] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const bottomRef = useRef(null);
  const textareaRef = useRef(null);
  const modeMenuRef = useRef(null);
  const activeChat = chats.find(c => c.id === activeChatId);
  const isNew = activeChat?.messages.length === 1;

  const isMobile = window.innerWidth <= 768;

  useEffect(() => {
    // On desktop, start with sidebar open
    if (window.innerWidth > 768) setSidebarOpen(true);
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [activeChat?.messages]);

  useEffect(() => {
    const ta = textareaRef.current;
    if (ta) {
      ta.style.height = "auto";
      ta.style.height = Math.min(ta.scrollHeight, 120) + "px";
    }
  }, [input]);

  useEffect(() => {
    const handler = (e) => {
      if (modeMenuRef.current && !modeMenuRef.current.contains(e.target)) {
        setModeMenuOpen(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  // Close sidebar when clicking overlay on mobile
  const handleOverlayClick = () => {
    if (window.innerWidth <= 768) setSidebarOpen(false);
  };

  const newChat = () => {
    const id = Date.now();
    setChats(prev => [
      { id, title: "New Chat", messages: [{ role: "assistant", content: WELCOME, sources: [], isWelcome: true }] },
      ...prev,
    ]);
    setActiveChatId(id);
    setInput("");
    setMode("chat");
    if (window.innerWidth <= 768) setSidebarOpen(false);
  };

  const selectChat = (id) => {
    setActiveChatId(id);
    if (window.innerWidth <= 768) setSidebarOpen(false);
  };

  const selectMode = (id) => { setMode(id); setModeMenuOpen(false); };
  const clearMode = () => setMode("chat");

  const filteredChats = chats.filter(c =>
    c.title.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const streamAnswer = useCallback(async (question, history, targetChatId) => {
    setLoading(true);

    try {
      const res = await fetch(`${API_URL}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question, history, mode }),
      });

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buf = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buf += decoder.decode(value, { stream: true });
        const lines = buf.split("\n");
        buf = lines.pop();

        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          try {
            const data = JSON.parse(line.slice(6));
            if (data.type === "sources") {
              setChats(prev => prev.map(c => {
                if (c.id !== targetChatId) return c;
                const msgs = [...c.messages];
                msgs[msgs.length - 1] = { ...msgs[msgs.length - 1], sources: data.sources };
                return { ...c, messages: msgs };
              }));
            }
            if (data.type === "token") {
              setChats(prev => prev.map(c => {
                if (c.id !== targetChatId) return c;
                const msgs = [...c.messages];
                msgs[msgs.length - 1] = {
                  ...msgs[msgs.length - 1],
                  content: msgs[msgs.length - 1].content + data.token,
                };
                return { ...c, messages: msgs };
              }));
              bottomRef.current?.scrollIntoView({ behavior: "smooth" });
            }
          } catch {}
        }
      }
    } catch {
      setChats(prev => prev.map(c => {
        if (c.id !== targetChatId) return c;
        const msgs = [...c.messages];
        msgs[msgs.length - 1] = { ...msgs[msgs.length - 1], content: "Something went wrong. Please try again." };
        return { ...c, messages: msgs };
      }));
    } finally {
      setLoading(false);
    }
  }, [mode]);

  const sendMessage = async (text) => {
    const question = (text || input).trim();
    if (!question || loading) return;

    const userMsg = { role: "user", content: question, sources: [] };
    const targetChatId = activeChatId;

    setChats(prev => prev.map(c => {
      if (c.id !== targetChatId) return c;
      const isFirst = c.messages.filter(m => m.role === "user").length === 0;
      return {
        ...c,
        title: isFirst ? question.slice(0, 36) : c.title,
        messages: [...c.messages, userMsg, { role: "assistant", content: "", sources: [] }],
      };
    }));

    setInput("");

    const history = [...activeChat.messages, userMsg]
      .slice(1).slice(-10)
      .map(m => ({ role: m.role, content: m.content }));

    await streamAnswer(question, history, targetChatId);
  };

  const retryLast = async () => {
    if (loading) return;
    const msgs = activeChat?.messages || [];
    const lastUserMsg = [...msgs].reverse().find(m => m.role === "user");
    if (!lastUserMsg) return;

    const targetChatId = activeChatId;

    setChats(prev => prev.map(c => {
      if (c.id !== targetChatId) return c;
      const updated = [...c.messages];
      if (updated[updated.length - 1].role === "assistant") {
        updated[updated.length - 1] = { role: "assistant", content: "", sources: [] };
      }
      return { ...c, messages: updated };
    }));

    const historyUpToUser = msgs
      .slice(1)
      .filter((_, i, arr) => {
        const lastUserIdx = arr.map(m => m.role).lastIndexOf("user");
        return i < lastUserIdx;
      })
      .map(m => ({ role: m.role, content: m.content }));

    await streamAnswer(lastUserMsg.content, historyUpToUser, targetChatId);
  };

  const handleKey = (e) => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessage(); }
  };

  const activeMode = MODES.find(m => m.id === mode);

  return (
    <div className="layout">

      {/* SIDEBAR OVERLAY (mobile) */}
      {sidebarOpen && (
        <div className="sidebar-overlay" onClick={handleOverlayClick} />
      )}

      {/* SIDEBAR */}
      <aside className={`sidebar ${sidebarOpen ? "open" : ""}`}>
        <div className="sidebar-header">
          {/* X button to close */}
          <button className="icon-btn close-btn" onClick={() => setSidebarOpen(false)}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <line x1="18" y1="6" x2="6" y2="18"/>
              <line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>

        {/* New Chat — flat, no button look */}
        <button className="sidebar-action" onClick={newChat}>
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="12" y1="5" x2="12" y2="19"/>
            <line x1="5" y1="12" x2="19" y2="12"/>
          </svg>
          New chat
        </button>

        {/* Search chats — flat, no button look */}
        <div className="sidebar-search-wrap">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="11" cy="11" r="8"/>
            <line x1="21" y1="21" x2="16.65" y2="16.65"/>
          </svg>
          <input
            className="sidebar-search"
            type="text"
            placeholder="Search chats"
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
          />
        </div>

        <div className="history-label">Recent</div>
        <div className="chat-history">
          {filteredChats.map(c => (
            <button
              key={c.id}
              className={`history-item ${c.id === activeChatId ? "active" : ""}`}
              onClick={() => selectChat(c.id)}
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
              </svg>
              <span>{c.title}</span>
            </button>
          ))}
        </div>

        <div className="sidebar-footer">
          <div className="brand-row">
            <div className="brand-dot" />
            <div>
              <div className="brand-name">Dag Bot</div>
              <div className="brand-sub">132 books · Bishop Dag Heward-Mills</div>
            </div>
          </div>
        </div>
      </aside>

      {/* MAIN */}
      <main className="main">

        {/* Mobile top bar with hamburger */}
        <div className="mobile-topbar">
          <button className="icon-btn" onClick={() => setSidebarOpen(true)}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="3" y1="6" x2="21" y2="6"/>
              <line x1="3" y1="12" x2="21" y2="12"/>
              <line x1="3" y1="18" x2="21" y2="18"/>
            </svg>
          </button>
        </div>

        <div className="messages">
          {isNew ? (
            <div className="welcome">
              <div className="welcome-wordmark">Dag Bot</div>
              <p className="welcome-sub">Explore 132 books by Bishop Dag Heward-Mills</p>
              <div className="suggestions">
                {SUGGESTIONS.map((s, i) => (
                  <button key={i} className="suggestion" onClick={() => sendMessage(s)}>
                    {s}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            activeChat?.messages.filter(msg => !msg.isWelcome).map((msg, i) => (
              <div key={i} className={`msg-row ${msg.role}`}>
                <div className="msg-body">
                  {msg.role === "user" ? (
                    <UserMessage content={msg.content} onEdit={(content) => { setInput(content); textareaRef.current?.focus(); }} />
                  ) : (
                    <>
                      <div className="assistant-text">
                        {msg.content
                          ? formatText(msg.content)
                          : loading && i === activeChat.messages.length - 1
                            ? <span className="blink">|</span>
                            : null}
                      </div>
                      {msg.content && !msg.isWelcome && (
                        <div className="msg-footer">
                          <MessageActions content={msg.content} onRetry={retryLast} />
                          <SourcesButton sources={msg.sources} />
                        </div>
                      )}
                    </>
                  )}
                </div>
              </div>
            ))
          )}
          <div ref={bottomRef} />
        </div>

        {/* Input */}
        <div className="input-area">
          <div className="input-container">
            <div className="mode-trigger-wrap" ref={modeMenuRef}>
              {mode === "chat" ? (
                <button className="mode-trigger" onClick={() => setModeMenuOpen(o => !o)} title="Select mode">
                  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <circle cx="12" cy="12" r="3"/>
                    <path d="M12 1v4M12 19v4M4.22 4.22l2.83 2.83M16.95 16.95l2.83 2.83M1 12h4M19 12h4M4.22 19.78l2.83-2.83M16.95 7.05l2.83-2.83"/>
                  </svg>
                </button>
              ) : (
                <button className="mode-tag" onClick={clearMode} title="Clear mode">
                  {activeMode?.label}
                  <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                    <line x1="18" y1="6" x2="6" y2="18"/>
                    <line x1="6" y1="6" x2="18" y2="18"/>
                  </svg>
                </button>
              )}

              {modeMenuOpen && (
                <div className="mode-menu">
                  <div className="mode-menu-title">Response mode</div>
                  {MODES.filter(m => m.id !== "chat").map(m => (
                    <button
                      key={m.id}
                      className={`mode-option ${mode === m.id ? "selected" : ""}`}
                      onClick={() => selectMode(m.id)}
                    >
                      <span className="mode-option-label">{m.label}</span>
                      <span className="mode-option-desc">{m.desc}</span>
                    </button>
                  ))}
                  <div className="mode-menu-divider" />
                  <button
                    className={`mode-option ${mode === "chat" ? "selected" : ""}`}
                    onClick={() => selectMode("chat")}
                  >
                    <span className="mode-option-label">Chat</span>
                    <span className="mode-option-desc">Ask anything</span>
                  </button>
                </div>
              )}
            </div>

            <textarea
              ref={textareaRef}
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={handleKey}
              placeholder="Ask anything from Bishop Dag's books..."
              rows={1}
              disabled={loading}
            />

            <button
              className="send-btn"
              onClick={() => sendMessage()}
              disabled={loading || !input.trim()}
            >
              <svg width="15" height="15" viewBox="0 0 24 24" fill="currentColor">
                <path d="M2 21L23 12 2 3v7l15 2-15 2v7z"/>
              </svg>
            </button>
          </div>
          <p className="footer-note">Dag Bot answers only from Bishop Dag Heward-Mills' books.</p>
        </div>
      </main>
    </div>
  );
}