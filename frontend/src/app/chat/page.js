'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import api from '@/services/api';
import styles from './chat.module.css';

export default function ChatPage() {
  const { user, loading: authLoading, logout } = useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();

  // State
  const [conversations, setConversations] = useState([]);
  const [activeConversationId, setActiveConversationId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);

  // Refs
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  // ── Load initial data ──────────────────────────────────────
  useEffect(() => {
    if (!authLoading && !user) {
      router.push('/login');
      return;
    }
    if (user) {
      loadConversations();
    }
  }, [user, authLoading]);

  // Handle URL params (prompt or conversation)
  useEffect(() => {
    if (!user) return;
    const conversationId = searchParams.get('conversation');
    const prompt = searchParams.get('prompt');

    if (conversationId) {
      loadConversation(conversationId);
    } else if (prompt) {
      setInput(prompt);
      // Clear the URL param
      window.history.replaceState({}, '', '/chat');
    }
  }, [user, searchParams]);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Auto-focus input
  useEffect(() => {
    if (!sending) inputRef.current?.focus();
  }, [sending, activeConversationId]);

  // ── API calls ──────────────────────────────────────────────
  const loadConversations = async () => {
    try {
      const data = await api.getConversations();
      setConversations(data);
    } catch (err) {
      console.error('Failed to load conversations:', err);
    }
  };

  const loadConversation = async (id) => {
    try {
      const data = await api.getConversation(id);
      setActiveConversationId(id);
      setMessages(data.messages || []);
    } catch (err) {
      console.error('Failed to load conversation:', err);
    }
  };

  const handleNewConversation = () => {
    setActiveConversationId(null);
    setMessages([]);
    setInput('');
    inputRef.current?.focus();
  };

  const handleDeleteConversation = async (id, e) => {
    e.stopPropagation();
    try {
      await api.deleteConversation(id);
      setConversations(prev => prev.filter(c => c.id !== id));
      if (activeConversationId === id) {
        handleNewConversation();
      }
    } catch (err) {
      console.error('Failed to delete conversation:', err);
    }
  };

  // ── Send message ───────────────────────────────────────────
  const handleSend = async (e) => {
    e?.preventDefault();
    const message = input.trim();
    if (!message || sending) return;

    setInput('');
    setSending(true);

    // Optimistically add user message
    const userMsg = {
      id: `temp-${Date.now()}`,
      role: 'user',
      content: message,
      created_at: new Date().toISOString(),
    };
    setMessages(prev => [...prev, userMsg]);

    try {
      const response = await api.sendMessage(message, activeConversationId);

      // Add assistant message
      const assistantMsg = {
        id: `resp-${Date.now()}`,
        role: 'assistant',
        content: response.message,
        created_at: new Date().toISOString(),
        status: response.status,
        task_id: response.task_id,
      };
      setMessages(prev => [...prev, assistantMsg]);

      if (!activeConversationId && response.conversation_id) {
        setActiveConversationId(response.conversation_id);
      }
      loadConversations();
    } catch (err) {
      const errorMsg = {
        id: `err-${Date.now()}`,
        role: 'assistant',
        content: `⚠️ ${err.message || 'Something went wrong. Please try again.'}`,
        created_at: new Date().toISOString(),
        isError: true,
      };
      setMessages(prev => [...prev, errorMsg]);
    } finally {
      setSending(false);
    }
  };

  const handleConfirmTask = async (taskId, msgId) => {
    try {
      const res = await api.confirmTask(taskId);
      setMessages(prev => prev.map(m => 
        m.id === msgId ? { ...m, status: 'completed', content: m.content + '\n\n' + res.message } : m
      ));
    } catch (err) {
      alert('Failed to confirm task: ' + err.message);
    }
  };

  const handleCancelTask = async (taskId, msgId) => {
    try {
      await api.cancelTask(taskId);
      setMessages(prev => prev.map(m => 
        m.id === msgId ? { ...m, status: 'cancelled', content: m.content + '\n\n❌ Action cancelled by user.' } : m
      ));
    } catch (err) {
      alert('Failed to cancel task: ' + err.message);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // ── Loading state ──────────────────────────────────────────
  if (authLoading || !user) {
    return (
      <div className={styles.loadingScreen}>
        <div className="spinner spinner-lg" />
      </div>
    );
  }

  return (
    <div className={styles.chatPage}>
      {/* Sidebar */}
      <aside className={`${styles.sidebar} ${sidebarOpen ? styles.sidebarOpen : ''}`}>
        <div className={styles.sidebarHeader}>
          <button
            className={styles.logoBtn}
            onClick={() => router.push('/dashboard')}
            title="Back to Dashboard"
          >
            <svg width="22" height="22" viewBox="0 0 32 32" fill="none">
              <rect width="32" height="32" rx="8" fill="url(#chat-logo)" />
              <path d="M10 16L14 20L22 12" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
              <defs>
                <linearGradient id="chat-logo" x1="0" y1="0" x2="32" y2="32">
                  <stop stopColor="#6c63ff" />
                  <stop offset="1" stopColor="#5a52d5" />
                </linearGradient>
              </defs>
            </svg>
          </button>
          <button
            className="btn btn-primary btn-sm"
            onClick={handleNewConversation}
            style={{ flex: 1 }}
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
              <line x1="12" y1="5" x2="12" y2="19" />
              <line x1="5" y1="12" x2="19" y2="12" />
            </svg>
            New Chat
          </button>
        </div>

        <div className={styles.sidebarConversations}>
          {conversations.map((conv) => (
            <button
              key={conv.id}
              className={`${styles.convItem} ${conv.id === activeConversationId ? styles.convItemActive : ''}`}
              onClick={() => loadConversation(conv.id)}
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
              </svg>
              <span className={styles.convItemTitle}>{conv.title}</span>
              <button
                className={styles.convDeleteBtn}
                onClick={(e) => handleDeleteConversation(conv.id, e)}
                title="Delete conversation"
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                  <line x1="18" y1="6" x2="6" y2="18" />
                  <line x1="6" y1="6" x2="18" y2="18" />
                </svg>
              </button>
            </button>
          ))}
        </div>

        <div className={styles.sidebarFooter}>
          <button className="btn btn-ghost btn-sm" onClick={logout} style={{ width: '100%' }}>
            Logout
          </button>
        </div>
      </aside>

      {/* Chat Area */}
      <main className={styles.chatMain}>
        {/* Mobile toggle */}
        <button
          className={styles.sidebarToggle}
          onClick={() => setSidebarOpen(!sidebarOpen)}
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
            <line x1="3" y1="6" x2="21" y2="6" />
            <line x1="3" y1="12" x2="21" y2="12" />
            <line x1="3" y1="18" x2="21" y2="18" />
          </svg>
        </button>

        {/* Messages */}
        <div className={styles.messagesContainer}>
          {messages.length === 0 ? (
            <div className={styles.emptyChat}>
              <div className={styles.emptyChatIcon}>
                <svg width="48" height="48" viewBox="0 0 32 32" fill="none">
                  <rect width="32" height="32" rx="8" fill="url(#empty-logo)" opacity="0.3" />
                  <path d="M10 16L14 20L22 12" stroke="var(--accent-primary)" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
                  <defs>
                    <linearGradient id="empty-logo" x1="0" y1="0" x2="32" y2="32">
                      <stop stopColor="#6c63ff" />
                      <stop offset="1" stopColor="#5a52d5" />
                    </linearGradient>
                  </defs>
                </svg>
              </div>
              <h2 className={styles.emptyChatTitle}>What can I help you with?</h2>
              <p className={styles.emptyChatDesc}>
                Ask me to manage your GitHub repos, create issues, branches, pull requests, and more.
              </p>
              <div className={styles.suggestions}>
                {[
                  'Show my GitHub repositories',
                  'Create an issue about dark mode',
                  'List open pull requests',
                  'Create a branch called feature/auth',
                ].map((suggestion) => (
                  <button
                    key={suggestion}
                    className={styles.suggestionBtn}
                    onClick={() => {
                      setInput(suggestion);
                      inputRef.current?.focus();
                    }}
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <div className={styles.messagesList}>
              {messages.map((msg, i) => (
                <div
                  key={msg.id}
                  className={`${styles.message} ${msg.role === 'user' ? styles.messageUser : styles.messageAssistant} ${msg.isError ? styles.messageError : ''}`}
                  style={{ animationDelay: `${i * 30}ms` }}
                >
                  <div className={styles.messageAvatar}>
                    {msg.role === 'user' ? (
                      <div className={styles.avatarUser}>
                        {user.name?.[0]?.toUpperCase() || 'U'}
                      </div>
                    ) : (
                      <div className={styles.avatarAgent}>
                        <svg width="18" height="18" viewBox="0 0 32 32" fill="none">
                          <rect width="32" height="32" rx="8" fill="url(#msg-logo)" />
                          <path d="M10 16L14 20L22 12" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
                          <defs>
                            <linearGradient id="msg-logo" x1="0" y1="0" x2="32" y2="32">
                              <stop stopColor="#6c63ff" />
                              <stop offset="1" stopColor="#5a52d5" />
                            </linearGradient>
                          </defs>
                        </svg>
                      </div>
                    )}
                  </div>
                  <div className={styles.messageContent}>
                    <span className={styles.messageRole}>
                      {msg.role === 'user' ? 'You' : 'Agent'}
                    </span>
                    <div className={styles.messageText}>
                      {msg.content}
                    </div>
                    {msg.status === 'awaiting_confirmation' && msg.task_id && (
                      <div className={styles.confirmationCard}>
                        <p className={styles.confirmationText}>Please confirm if you want to proceed with this action.</p>
                        <div className={styles.confirmationActions}>
                          <button 
                            className="btn btn-primary btn-sm" 
                            onClick={() => handleConfirmTask(msg.task_id, msg.id)}
                          >
                            Proceed
                          </button>
                          <button 
                            className="btn btn-secondary btn-sm" 
                            onClick={() => handleCancelTask(msg.task_id, msg.id)}
                          >
                            Cancel
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              ))}

              {/* Typing indicator */}
              {sending && (
                <div className={`${styles.message} ${styles.messageAssistant}`}>
                  <div className={styles.messageAvatar}>
                    <div className={styles.avatarAgent}>
                      <svg width="18" height="18" viewBox="0 0 32 32" fill="none">
                        <rect width="32" height="32" rx="8" fill="url(#typing-logo)" />
                        <path d="M10 16L14 20L22 12" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
                        <defs>
                          <linearGradient id="typing-logo" x1="0" y1="0" x2="32" y2="32">
                            <stop stopColor="#6c63ff" />
                            <stop offset="1" stopColor="#5a52d5" />
                          </linearGradient>
                        </defs>
                      </svg>
                    </div>
                  </div>
                  <div className={styles.messageContent}>
                    <span className={styles.messageRole}>Agent</span>
                    <div className={styles.typingIndicator}>
                      <span className={styles.typingDot} />
                      <span className={styles.typingDot} />
                      <span className={styles.typingDot} />
                    </div>
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* Input Area */}
        <div className={styles.inputArea}>
          <form onSubmit={handleSend} className={styles.inputForm}>
            <textarea
              ref={inputRef}
              className={styles.chatInput}
              placeholder="Type a command..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              rows={1}
              disabled={sending}
            />
            <button
              type="submit"
              className={`btn btn-primary ${styles.sendBtn}`}
              disabled={!input.trim() || sending}
            >
              {sending ? (
                <span className="spinner" />
              ) : (
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <line x1="22" y1="2" x2="11" y2="13" />
                  <polygon points="22 2 15 22 11 13 2 9 22 2" />
                </svg>
              )}
            </button>
          </form>
        </div>
      </main>
    </div>
  );
}
