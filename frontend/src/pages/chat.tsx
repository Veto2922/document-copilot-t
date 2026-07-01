import React, { useState, useEffect, useRef, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useAuth } from "@/lib/auth-context";
import { api, type ChatThread, type ChatMessage } from "@/lib/api";
import { env } from "@/lib/env";
import { getAccessToken } from "@/lib/supabase";
import {
  Plus,
  MessageSquare,
  Send,
  LogOut,
  User,
  Loader2,
  Sparkles,
  Cpu,
  History,
  Terminal,
  ShieldCheck,
  AlertCircle
} from "lucide-react";
import { Button } from "@/components/ui/button";

export const Chat: React.FC = () => {
  const { user, signOut } = useAuth();
  const { threadId: urlThreadId } = useParams<{ threadId: string }>();
  const navigate = useNavigate();

  const [threads, setThreads] = useState<ChatThread[]>([]);
  const [activeThreadId, setActiveThreadId] = useState<string | null>(urlThreadId ?? null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputText, setInputText] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  
  const [loadingThreads, setLoadingThreads] = useState(true);
  const [loadingMessages, setLoadingMessages] = useState(false);
  const [creatingThread, setCreatingThread] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll messages list to bottom
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isStreaming]);

  // Navigate to thread URL when activeThreadId changes (user selection)
  const selectThread = useCallback((threadId: string) => {
    setActiveThreadId(threadId);
    navigate(`/chat/${threadId}`, { replace: true });
  }, [navigate]);

  // Sync activeThreadId when URL param changes (browser back/forward)
  useEffect(() => {
    if (urlThreadId && urlThreadId !== activeThreadId) {
      setActiveThreadId(urlThreadId);
    }
  }, [urlThreadId]); // eslint-disable-line react-hooks/exhaustive-deps

  // Load user threads on mount
  useEffect(() => {
    const loadThreads = async () => {
      setLoadingThreads(true);
      setError(null);
      try {
        const data = await api.getThreads();
        setThreads(data);
        // If URL has a thread, keep it; otherwise select the most recent
        if (!urlThreadId && data.length > 0) {
          selectThread(data[0].id);
        }
      } catch (err: unknown) {
        console.error("Failed to load threads:", err);
        setError("Failed to load conversation threads.");
      } finally {
        setLoadingThreads(false);
      }
    };
    loadThreads();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Fetch messages when active thread changes
  useEffect(() => {
    if (activeThreadId) {
      const loadMessages = async (threadId: string) => {
        setLoadingMessages(true);
        setError(null);
        try {
          const data = await api.getMessages(threadId);
          setMessages(data);
        } catch (err: unknown) {
          console.error("Failed to load messages:", err);
          setError("Failed to load message history.");
        } finally {
          setLoadingMessages(false);
        }
      };
      loadMessages(activeThreadId);
    } else {
      setMessages([]);
    }
  }, [activeThreadId]);

  const handleCreateThread = async () => {
    setCreatingThread(true);
    setError(null);
    try {
      const count = threads.length + 1;
      const newThread = await api.createThread(`Analysis Thread #${count}`);
      setThreads((prev) => [newThread, ...prev]);
      selectThread(newThread.id);
    } catch (err: unknown) {
      console.error("Failed to create thread:", err);
      setError("Failed to create a new thread.");
    } finally {
      setCreatingThread(false);
    }
  };

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputText.trim() || !activeThreadId || isStreaming) return;

    const userText = inputText.trim();
    setInputText("");
    setError(null);

    const newUserMessage: ChatMessage = {
      id: `temp-user-${Date.now()}`,
      thread_id: activeThreadId,
      role: "user",
      content: userText,
      created_at: new Date().toISOString(),
    };

    // Add user message to UI state immediately
    setMessages((prev) => [...prev, newUserMessage]);
    setIsStreaming(true);

    const tempAssistantId = `temp-assistant-${Date.now()}`;
    const newAssistantMessage: ChatMessage = {
      id: tempAssistantId,
      thread_id: activeThreadId,
      role: "assistant",
      content: "",
      created_at: new Date().toISOString(),
    };

    // Append streaming assistant placeholder to message list
    setMessages((prev) => [...prev, newAssistantMessage]);

    try {
      const token = await getAccessToken();
      const baseUrl = env.VITE_API_BASE_URL.replace(/\/$/, "");

      // Gather non-temporary messages for endpoint input context
      const apiMessages = messages
        .filter((m) => !m.id.startsWith("temp-"))
        .concat(newUserMessage)
        .map((m) => ({
          role: m.role,
          content: m.content,
        }));

      const response = await fetch(`${baseUrl}/chat/stream`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { "Authorization": `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({
          messages: apiMessages,
          thread_id: activeThreadId,
        }),
      });

      if (!response.ok) {
        const errText = await response.text();
        throw new Error(errText || `Server error code ${response.status}`);
      }

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error("Stream reader not supported by response");
      }

      const decoder = new TextDecoder();
      let streamContent = "";

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        streamContent += chunk;

        // Keep updating streaming assistant text bubble
        setMessages((prev) =>
          prev.map((m) =>
            m.id === tempAssistantId ? { ...m, content: streamContent } : m
          )
        );
      }
    } catch (err: unknown) {
      console.error("Streaming error:", err);
      const errMsg = err instanceof Error ? err.message : "An error occurred during communication.";
      setMessages((prev) =>
        prev.map((m) =>
          m.id === tempAssistantId
            ? { ...m, content: `Error: ${errMsg}. Please try again.` }
            : m
        )
      );
      setError(errMsg);
    } finally {
      setIsStreaming(false);
      // Retrieve authoritative message logs from DB to sync correct ids/timestamps
      try {
        const syncedMessages = await api.getMessages(activeThreadId);
        setMessages(syncedMessages);
      } catch (syncErr) {
        console.error("Failed to sync message history:", syncErr);
      }
    }
  };

  const activeThread = threads.find((t) => t.id === activeThreadId);

  return (
    <div className="flex h-screen w-screen bg-[#060814] font-sans text-slate-200 overflow-hidden relative">
      {/* Background visual cues */}
      <div className="absolute top-0 left-80 w-[calc(100vw-20rem)] h-[500px] bg-gradient-to-b from-indigo-500/5 to-transparent pointer-events-none"></div>
      <div className="absolute bottom-0 right-0 w-[600px] h-[600px] bg-[radial-gradient(circle_at_bottom_right,rgba(99,102,241,0.06),transparent_70%)] pointer-events-none"></div>

      {/* Left Sidebar */}
      <aside className="w-80 border-r border-slate-800/40 bg-[#0b0f19]/70 backdrop-blur-xl flex flex-col justify-between shrink-0 z-10">
        <div className="flex flex-col h-full overflow-hidden">
          {/* Header */}
          <div className="p-5 border-b border-slate-800/40 flex items-center gap-3">
            <div className="h-9 w-9 rounded-xl bg-indigo-600/10 flex items-center justify-center border border-indigo-500/25 text-indigo-400 shadow-[0_0_15px_rgba(99,102,241,0.15)]">
              <Cpu className="h-4 w-4" />
            </div>
            <div>
              <h1 className="font-bold text-sm text-slate-100 tracking-tight">Document Copilot</h1>
              <p className="text-[10px] text-slate-500 uppercase tracking-wider font-semibold">SEC Analytics</p>
            </div>
          </div>

          {/* New Chat Button */}
          <div className="p-4 shrink-0">
            <Button
              onClick={handleCreateThread}
              disabled={creatingThread}
              className="w-full justify-center gap-2 bg-indigo-600/10 border border-indigo-500/30 text-indigo-300 hover:bg-indigo-600 hover:text-white font-medium py-5 rounded-xl shadow-sm transition-all"
            >
              {creatingThread ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Plus className="h-4 w-4" />
              )}
              <span>New Analysis</span>
            </Button>
          </div>

          {/* Thread List */}
          <div className="flex-1 overflow-y-auto px-3 py-2 space-y-1 scrollbar-thin scrollbar-thumb-slate-800">
            <div className="px-3 mb-2 flex items-center gap-1.5 text-[10px] font-semibold text-slate-500 uppercase tracking-wider">
              <History className="h-3 w-3" />
              <span>Analyses Log</span>
            </div>

            {loadingThreads ? (
              <div className="flex flex-col items-center justify-center py-8 space-y-2 text-slate-500">
                <Loader2 className="h-5 w-5 animate-spin text-indigo-500" />
                <span className="text-xs">Loading logs...</span>
              </div>
            ) : threads.length === 0 ? (
              <div className="px-3 py-6 text-center text-xs text-slate-600 italic">
                No search threads yet.
              </div>
            ) : (
              threads.map((thread) => {
                const isActive = thread.id === activeThreadId;
                return (
                  <button
                    key={thread.id}
                    onClick={() => selectThread(thread.id)}
                    className={`w-full flex items-center gap-3 px-3.5 py-3 rounded-xl text-left transition-all ${
                      isActive
                        ? "bg-indigo-600/10 border border-indigo-500/25 text-indigo-300 shadow-[0_2px_12px_rgba(99,102,241,0.05)]"
                        : "border border-transparent text-slate-400 hover:bg-white/[0.02] hover:text-slate-200"
                    }`}
                  >
                    <MessageSquare className={`h-4 w-4 shrink-0 ${isActive ? "text-indigo-400" : "text-slate-500"}`} />
                    <span className="truncate text-xs font-medium flex-1">{thread.title || "Untitled Thread"}</span>
                  </button>
                );
              })
            )}
          </div>
        </div>

        {/* User Footer Panel */}
        <div className="p-4 border-t border-slate-800/40 bg-[#090c15]/50 flex flex-col gap-3">
          <div className="flex items-center gap-3 px-1">
            <div className="h-8 w-8 rounded-lg bg-indigo-500/10 flex items-center justify-center text-indigo-400 border border-indigo-500/20">
              <User className="h-4 w-4" />
            </div>
            <div className="min-w-0 flex-1">
              <p className="text-xs font-semibold text-slate-300 truncate">{user?.email}</p>
              <p className="text-[10px] text-emerald-400 flex items-center gap-1">
                <ShieldCheck className="h-3 w-3 shrink-0" /> Verified Agent
              </p>
            </div>
          </div>
          <Button
            onClick={() => signOut()}
            variant="ghost"
            className="w-full text-slate-500 hover:text-slate-300 hover:bg-white/[0.02] justify-start gap-2 py-4 rounded-xl text-xs"
          >
            <LogOut className="h-3.5 w-3.5" />
            <span>Sign Out</span>
          </Button>
        </div>
      </aside>

      {/* Main Chat Workspace */}
      <main className="flex-1 flex flex-col min-w-0 h-full relative z-10">
        {/* Workspace Top Header */}
        <header className="h-16 border-b border-slate-800/40 px-6 flex items-center justify-between bg-[#060814]/30 backdrop-blur-md">
          <div className="flex items-center gap-2">
            <Terminal className="h-4 w-4 text-indigo-400" />
            <span className="text-xs font-mono text-slate-400">workspace /</span>
            <span className="text-xs font-semibold text-slate-200 truncate max-w-sm">
              {activeThread ? activeThread.title : "Unassigned"}
            </span>
          </div>
          {activeThreadId && (
            <div className="text-[10px] px-2 py-0.5 rounded-full border border-indigo-500/20 bg-indigo-500/5 text-indigo-400 font-mono">
              Thread: {activeThreadId.slice(0, 8)}...
            </div>
          )}
        </header>

        {/* Work Area Message List */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {error && (
            <div className="flex items-start gap-3 p-4 rounded-xl border border-rose-500/20 bg-rose-500/5 text-rose-300 text-xs max-w-2xl mx-auto">
              <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
              <div className="flex-1">
                <span className="font-semibold">Operation Exception:</span> {error}
              </div>
            </div>
          )}

          {!activeThreadId ? (
            <div className="h-full flex flex-col items-center justify-center p-8 text-center max-w-md mx-auto space-y-6">
              <div className="h-14 w-14 rounded-2xl bg-indigo-500/10 flex items-center justify-center border border-indigo-500/20 text-indigo-400 shadow-[0_0_20px_rgba(99,102,241,0.08)]">
                <Sparkles className="h-6 w-6" />
              </div>
              <div className="space-y-2">
                <h2 className="text-md font-bold text-slate-200">Start Filing Search Query</h2>
                <p className="text-xs text-slate-500 leading-relaxed">
                  Select a past discussion thread from the sidebar ledger or create a new session to begin querying consolidated SEC filings.
                </p>
              </div>
              <Button
                onClick={handleCreateThread}
                disabled={creatingThread}
                className="bg-indigo-600 hover:bg-indigo-500 font-semibold text-white px-5 rounded-xl text-xs transition-all shadow-md shadow-indigo-600/10"
              >
                <Plus className="mr-1.5 h-3.5 w-3.5" />
                <span>Initialize Workspace</span>
              </Button>
            </div>
          ) : loadingMessages && messages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center space-y-2 text-slate-500">
              <Loader2 className="h-6 w-6 animate-spin text-indigo-500" />
              <span className="text-xs">Accessing history ledger...</span>
            </div>
          ) : (
            <div className="max-w-3xl mx-auto space-y-6">
              {messages.map((message) => {
                const isUser = message.role === "user";
                return (
                  <div
                    key={message.id}
                    className={`flex items-start gap-4 ${isUser ? "justify-end" : "justify-start"}`}
                  >
                    {!isUser && (
                      <div className="h-8 w-8 rounded-lg bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400 shrink-0">
                        <Cpu className="h-4 w-4" />
                      </div>
                    )}
                    <div
                      className={`relative px-4 py-3 rounded-2xl text-xs leading-relaxed max-w-[80%] ${
                        isUser
                          ? "bg-indigo-600 text-white rounded-tr-sm shadow-md shadow-indigo-600/10"
                          : "bg-[#0b0f19]/80 border border-slate-800/60 text-slate-200 rounded-tl-sm"
                      }`}
                    >
                      <p className="whitespace-pre-wrap">{message.content || (isStreaming && message.id.startsWith("temp-") ? "..." : "")}</p>
                    </div>
                    {isUser && (
                      <div className="h-8 w-8 rounded-lg bg-slate-800/40 border border-slate-700/40 flex items-center justify-center text-slate-300 shrink-0">
                        <User className="h-4 w-4" />
                      </div>
                    )}
                  </div>
                );
              })}

              {/* Scroll anchor */}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* Input Panel */}
        {activeThreadId && (
          <div className="p-6 bg-gradient-to-t from-[#060814] to-transparent shrink-0">
            <form onSubmit={handleSendMessage} className="max-w-3xl mx-auto">
              <div className="relative flex items-center bg-[#0a0d16] border border-slate-800 rounded-2xl p-1.5 focus-within:border-indigo-500/40 focus-within:ring-2 focus-within:ring-indigo-500/5 transition-all">
                <input
                  type="text"
                  value={inputText}
                  onChange={(e) => setInputText(e.target.value)}
                  placeholder="Ask a question about the corpus filings (e.g. 'Summarize risk factors for NVDA 2024')"
                  disabled={isStreaming}
                  className="flex-1 bg-transparent border-0 ring-0 focus:ring-0 focus:outline-none px-4 py-3 text-xs text-slate-200 placeholder-slate-500"
                />
                <Button
                  type="submit"
                  disabled={isStreaming || !inputText.trim()}
                  className="h-10 w-10 rounded-xl bg-indigo-600 hover:bg-indigo-500 flex items-center justify-center text-white transition-all shadow-md shadow-indigo-600/15 disabled:opacity-40 disabled:hover:bg-indigo-600 shrink-0"
                >
                  {isStreaming ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Send className="h-4 w-4" />
                  )}
                </Button>
              </div>
            </form>
          </div>
        )}
      </main>
    </div>
  );
};
