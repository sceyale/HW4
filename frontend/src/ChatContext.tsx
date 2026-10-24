import { createContext, useCallback, useContext, useEffect, useRef, useState, type ReactNode } from "react";
import { clearChatHistory, fetchChatHistory, sendChat } from "./api.ts";
import { useNavigate } from "react-router-dom";
import { useAuth } from "./AuthContext.tsx";
import type { ChatMatches, ChatMessage, ChatResponse, PageContext } from "./types.ts";

const WELCOME: ChatMessage = {
  id: 0,
  role: "assistant",
  content: "Hi! I'm the Campus Customs shop assistant. Ask me about products, sizes, stock or prices.",
};
const GUEST_HISTORY = 10;   // turns the browser sends for guests (logged-in history lives on the server)

function toMatches(res: ChatResponse, version: number): ChatMatches {
  const s = res.search;
  const isSearch = res.display === "search_results" && s !== null;
  const label = isSearch
    ? s!.category && !s!.query ? s!.category : s!.query ? `"${s!.query}"` + (s!.category ? ` in ${s!.category}` : "") : "Your search"
    : "Picked by the shop assistant";
  return { products: res.products, label, total: isSearch ? s!.total_matches : res.products.length, isSearch, version };
}

// Filled in by the Products page so the agent knows the category filter and which cards are on screen.
export type PageInfo = { category: string | null; visible_product_ids: string[] };
const EMPTY_PAGE_INFO: PageInfo = { category: null, visible_product_ids: [] };

type ChatState = {
  open: boolean;
  setOpen: (open: boolean) => void;
  pendingQuestion: string | null;          // set by ask(); the widget sends it with page context
  ask: (question: string) => void;
  takePending: () => string | null;
  messages: ChatMessage[];
  matches: ChatMatches | null;         // products from the latest reply, shown on the page
  sending: boolean;
  send: (text: string, page: PageContext) => Promise<void>;
  pageInfo: PageInfo;
  setPageInfo: (info: PageInfo) => void;
  clear: () => Promise<void>;
  clearMatches: () => void;
};

const ChatContext = createContext<ChatState | null>(null);

export function ChatProvider({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth();
  const [messages, setMessages] = useState<ChatMessage[]>([WELCOME]);
  const [matches, setMatches] = useState<ChatMatches | null>(null);
  const navigate = useNavigate();
  const version = useRef(0);
  const [sending, setSending] = useState(false);
  const [pageInfo, setPageInfoState] = useState<PageInfo>(EMPTY_PAGE_INFO);
  const [open, setOpen] = useState(false);
  const [pendingQuestion, setPending] = useState<string | null>(null);
  const ask = useCallback((question: string) => { setPending(question); setOpen(true); }, []);
  const takePending = useCallback(() => {
    const q = pendingQuestion;
    setPending(null);
    return q;
  }, [pendingQuestion]);
  const setPageInfo = useCallback((info: PageInfo) => setPageInfoState(info), []);
  const nextId = useRef(1);

  // Load saved history when a shopper logs in; reset when they log out.
  useEffect(() => {
    if (loading) return;
    setMatches(null);
    if (!user) {
      setMessages([WELCOME]);
      return;
    }
    fetchChatHistory().then((items) => {
      const greeting = { ...WELCOME, content: `Welcome back, ${user.first_name ?? user.name}! What can I help you find?` };
      setMessages([greeting, ...items.map((m) => ({ id: m.id, role: m.role, content: m.content, products: m.products }))]);
    });
  }, [user, loading]);

  const send = useCallback(async (text: string, page: PageContext) => {
    const userMsg: ChatMessage = { id: -nextId.current++, role: "user", content: text };
    const history = user
      ? undefined
      : messages.filter((m) => m.id !== 0 && !m.error).slice(-GUEST_HISTORY)
          .map((m) => ({ role: m.role, content: m.content }));
    setMessages((m) => [...m, userMsg]);
    setSending(true);
    try {
      const res = await sendChat({ message: text, page, history });
      setMessages((m) => [...m, { id: -nextId.current++, role: "assistant", content: res.reply, products: res.products, display: res.display }]);
      if (res.products.length) {
        setMatches(toMatches(res, ++version.current));
        // A browse search ("what hoodies do you have?") updates the Products page with every match.
        if (res.display === "search_results") navigate("/products");
      }
    } catch (err) {
      setMessages((m) => [...m, { id: -nextId.current++, role: "assistant", content: (err as Error).message, error: true }]);
    } finally {
      setSending(false);
    }
  }, [messages, user, navigate]);

  const clear = useCallback(async () => {
    if (user) await clearChatHistory();
    setMessages([WELCOME]);
    setMatches(null);
  }, [user]);

  const clearMatches = useCallback(() => setMatches(null), []);

  return (
    <ChatContext.Provider value={{ messages, matches, sending, send, clear, clearMatches, pageInfo, setPageInfo,
        open, setOpen, pendingQuestion, ask, takePending }}>
      {children}
    </ChatContext.Provider>
  );
}

export function useChat(): ChatState {
  const ctx = useContext(ChatContext);
  if (!ctx) throw new Error("useChat must be used inside <ChatProvider>");
  return ctx;
}
