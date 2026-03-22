import { useState, useRef, useEffect } from 'react';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  toolsUsed?: string[];
}

interface Props {
  view?: 'dashboard' | 'map';
}

const DASHBOARD_QUESTIONS = [
  "Why is Strait of Hormuz critical?",
  "Why is Brent crude above $100?",
  "What is the biggest risk right now?",
  "Why is Cape of Good Hope disrupted?",
  "Explain the energy risk score",
];

const MAP_QUESTIONS = [
  "How many vessels are in the Hormuz zone right now?",
  "Are there any dark or suspicious vessels?",
  "Show me slow-moving tankers near Hormuz",
  "What's the vessel traffic trend in the last 48 hours?",
  "Which zones have the highest maritime risk?",
];

export default function AskAnalyst({ view = 'dashboard' }: Props) {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const isMapView = view === 'map';
  const suggestedQuestions = isMapView ? MAP_QUESTIONS : DASHBOARD_QUESTIONS;
  const apiEndpoint = isMapView ? '/api/v1/ai/ask' : '/api/ask';

  const askQuestion = async (question: string) => {
    if (!question.trim() || loading) return;

    const userMsg: Message = { role: 'user', content: question };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    try {
      const res = await fetch(apiEndpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question }),
      });
      const data = await res.json();

      const assistantMsg: Message = {
        role: 'assistant',
        content: data.answer,
        toolsUsed: data.tools_used,
      };
      setMessages(prev => [...prev, assistantMsg]);
    } catch {
      setMessages(prev => [...prev, { role: 'assistant', content: 'Unable to reach the analyst. Please try again.' }]);
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) {
    return (
      <button
        onClick={() => setIsOpen(true)}
        className="fixed bottom-6 right-6 z-[2000] flex items-center gap-2 px-5 py-3 rounded-full bg-accent text-white font-semibold text-[13px] shadow-lg hover:shadow-xl hover:scale-105 transition-all"
      >
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
        </svg>
        Ask Analyst
      </button>
    );
  }

  return (
    <div className="fixed bottom-6 right-6 z-[2000] w-[420px] flex flex-col rounded-2xl bg-bg-card border border-border shadow-2xl overflow-hidden"
         style={{ height: '520px' }}>
      {/* Header */}
      <div className="flex items-center justify-between px-5 py-3 border-b border-border bg-header-bg">
        <div className="flex items-center gap-2.5">
          <div className="w-2 h-2 rounded-full bg-accent animate-live" />
          <span className="font-heading font-bold text-[13px] text-text-primary">SupplyWatch Analyst</span>
          {isMapView && (
            <span className="text-[9px] text-cyan-400 uppercase tracking-wider font-semibold px-1.5 py-0.5 rounded bg-cyan-400/10 border border-cyan-400/20">
              Vessel AI
            </span>
          )}
          {!isMapView && (
            <span className="text-[9px] text-text-dim uppercase tracking-wider">AI-Powered</span>
          )}
        </div>
        <button
          onClick={() => setIsOpen(false)}
          className="text-text-dim hover:text-text-primary transition-colors text-lg leading-none"
        >
          ×
        </button>
      </div>

      {/* Messages */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto p-4 flex flex-col gap-3">
        {messages.length === 0 && (
          <div className="flex flex-col gap-2">
            <p className="text-[12px] text-text-muted mb-2">
              {isMapView
                ? 'Ask me about vessels, maritime traffic, dark ships, or zone risks:'
                : 'Ask me about any metric, route, or risk on the dashboard:'}
            </p>
            {suggestedQuestions.map(q => (
              <button
                key={q}
                onClick={() => askQuestion(q)}
                className="text-left px-3 py-2 rounded-lg text-[12px] text-text-secondary bg-pill-bg border border-border hover:border-accent/30 hover:bg-accent/5 transition-all"
              >
                {q}
              </button>
            ))}
          </div>
        )}

        {messages.map((msg, i) => (
          <div key={i} className="flex flex-col gap-1">
            <div
              className={`max-w-[90%] px-3.5 py-2.5 rounded-xl text-[12.5px] leading-relaxed whitespace-pre-wrap ${
                msg.role === 'user'
                  ? 'self-end bg-accent text-white rounded-br-sm'
                  : 'self-start bg-pill-bg border border-border text-text-secondary rounded-bl-sm'
              }`}
            >
              {msg.content}
            </div>
            {msg.role === 'assistant' && msg.toolsUsed && msg.toolsUsed.length > 0 && (
              <div className="self-start flex items-center gap-1 ml-1">
                {msg.toolsUsed.map(tool => (
                  <span key={tool} className="text-[9px] text-text-dim bg-pill-bg border border-border rounded px-1.5 py-0.5">
                    {tool.replace(/_/g, ' ')}
                  </span>
                ))}
              </div>
            )}
          </div>
        ))}

        {loading && (
          <div className="self-start px-3.5 py-2.5 rounded-xl bg-pill-bg border border-border rounded-bl-sm">
            <div className="flex items-center gap-2">
              <div className="flex gap-1">
                <div className="w-1.5 h-1.5 rounded-full bg-text-dim animate-bounce" style={{ animationDelay: '0ms' }} />
                <div className="w-1.5 h-1.5 rounded-full bg-text-dim animate-bounce" style={{ animationDelay: '150ms' }} />
                <div className="w-1.5 h-1.5 rounded-full bg-text-dim animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
              {isMapView && <span className="text-[10px] text-text-dim">Querying vessel data...</span>}
            </div>
          </div>
        )}
      </div>

      {/* Input */}
      <div className="px-4 py-3 border-t border-border">
        <form
          onSubmit={e => { e.preventDefault(); askQuestion(input); }}
          className="flex gap-2"
        >
          <input
            type="text"
            value={input}
            onChange={e => setInput(e.target.value)}
            placeholder={isMapView ? "Ask about vessels, zones, traffic..." : "Ask about any risk metric..."}
            className="flex-1 px-3.5 py-2 rounded-lg bg-bg-input border border-border text-[12px] text-text-primary placeholder:text-text-dim focus:outline-none focus:border-accent/40 transition-colors"
            disabled={loading}
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="px-3.5 py-2 rounded-lg bg-accent text-white text-[12px] font-semibold disabled:opacity-40 hover:bg-accent/90 transition-all"
          >
            Ask
          </button>
        </form>
      </div>
    </div>
  );
}
