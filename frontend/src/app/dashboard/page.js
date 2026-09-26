'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import api from '@/services/api';
import styles from './dashboard.module.css';

// ── Platform icons as inline SVGs ────────────────────────────
const PLATFORM_ICONS = {
  github: (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
      <path d="M12 2C6.477 2 2 6.477 2 12c0 4.42 2.865 8.17 6.839 9.49.5.092.682-.217.682-.482 0-.237-.009-.866-.013-1.7-2.782.604-3.369-1.34-3.369-1.34-.454-1.156-1.11-1.464-1.11-1.464-.908-.62.069-.608.069-.608 1.003.07 1.531 1.03 1.531 1.03.892 1.529 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.11-4.555-4.943 0-1.091.39-1.984 1.029-2.683-.103-.253-.446-1.27.098-2.647 0 0 .84-.269 2.75 1.025A9.578 9.578 0 0112 6.836c.85.004 1.705.115 2.504.337 1.909-1.294 2.747-1.025 2.747-1.025.546 1.377.203 2.394.1 2.647.64.699 1.028 1.592 1.028 2.683 0 3.842-2.339 4.687-4.566 4.935.359.309.678.919.678 1.852 0 1.336-.012 2.415-.012 2.743 0 .267.18.578.688.48C19.138 20.167 22 16.418 22 12c0-5.523-4.477-10-10-10z" />
    </svg>
  ),
  linkedin: (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
      <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 01-2.063-2.065 2.064 2.064 0 112.063 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z" />
    </svg>
  ),
  mail: (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="2" y="4" width="20" height="16" rx="2" />
      <path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7" />
    </svg>
  ),
  calendar: (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="4" width="18" height="18" rx="2" ry="2" />
      <line x1="16" y1="2" x2="16" y2="6" />
      <line x1="8" y1="2" x2="8" y2="6" />
      <line x1="3" y1="10" x2="21" y2="10" />
    </svg>
  ),
};

export default function DashboardPage() {
  const { user, loading: authLoading, logout } = useAuth();
  const router = useRouter();
  const [connections, setConnections] = useState([]);
  const [conversations, setConversations] = useState([]);
  const [loadingData, setLoadingData] = useState(true);

  useEffect(() => {
    if (!authLoading && !user) {
      router.push('/login');
      return;
    }
    if (user) {
      loadDashboardData();
    }
  }, [user, authLoading]);

  const loadDashboardData = async () => {
    try {
      const [conns, convs] = await Promise.all([
        api.getConnections().catch(() => []),
        api.getConversations().catch(() => []),
      ]);
      setConnections(conns);
      setConversations(convs);
    } finally {
      setLoadingData(false);
    }
  };

  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return 'Good morning';
    if (hour < 17) return 'Good afternoon';
    return 'Good evening';
  };

  if (authLoading || !user) {
    return (
      <div className={styles.loadingScreen}>
        <div className="spinner spinner-lg" />
      </div>
    );
  }

  const handleConnect = async (platform) => {
    try {
      if (platform === 'github') {
        const response = await api.request('POST', '/api/connections/github/auth');
        window.location.href = response.url;
      }
    } catch (err) {
      console.error('Failed to get auth URL', err);
      alert('Failed to start connection process.');
    }
  };

  const handleDisconnect = async (platform) => {
    if (!window.confirm(`Are you sure you want to disconnect ${platform}?`)) return;
    try {
      await api.request('DELETE', `/api/connections/${platform}`);
      loadDashboardData(); // Refresh list
    } catch (err) {
      console.error('Failed to disconnect', err);
      alert('Failed to disconnect platform.');
    }
  };

  return (
    <div className={styles.dashboardPage}>
      {/* Header */}
      <header className={styles.header}>
        <div className={styles.headerLeft}>
          <div className={styles.logoSmall}>
            <svg width="24" height="24" viewBox="0 0 32 32" fill="none">
              <rect width="32" height="32" rx="8" fill="url(#dash-logo)" />
              <path d="M10 16L14 20L22 12" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
              <defs>
                <linearGradient id="dash-logo" x1="0" y1="0" x2="32" y2="32">
                  <stop stopColor="#6c63ff" />
                  <stop offset="1" stopColor="#5a52d5" />
                </linearGradient>
              </defs>
            </svg>
          </div>
          <span className={styles.headerTitle}>Personal AI Agent</span>
        </div>
        <div className={styles.headerRight}>
          <button className="btn btn-ghost btn-sm" onClick={() => router.push('/chat')}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
            </svg>
            Chat
          </button>
          <button className="btn btn-ghost btn-sm" onClick={logout}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
              <polyline points="16 17 21 12 16 7" />
              <line x1="21" y1="12" x2="9" y2="12" />
            </svg>
            Logout
          </button>
        </div>
      </header>

      {/* Main Content */}
      <main className={styles.main}>
        {/* Greeting */}
        <section className={styles.greeting}>
          <h1 className={styles.greetingTitle}>
            {getGreeting()}, {user.name?.split(' ')[0]}!
          </h1>
          <p className={styles.greetingSubtitle}>
            What would you like to accomplish today?
          </p>
        </section>

        {/* Connected Platforms */}
        <section className={styles.section}>
          <h2 className={styles.sectionTitle}>Connected Platforms</h2>
          <div className={styles.platformGrid}>
            {connections.map((platform, i) => (
              <div
                key={platform.platform}
                className={`${styles.platformCard} glass-card`}
                style={{ animationDelay: `${i * 80}ms` }}
              >
                <div className={styles.platformIcon}>
                  {PLATFORM_ICONS[platform.icon] || PLATFORM_ICONS.github}
                </div>
                <div className={styles.platformInfo}>
                  <h3 className={styles.platformName}>{platform.name}</h3>
                  <p className={styles.platformDesc}>{platform.description}</p>
                </div>
                <div className={styles.platformStatus}>
                  {platform.connected ? (
                    <button className="btn btn-ghost btn-sm" onClick={() => handleDisconnect(platform.platform)}>Disconnect</button>
                  ) : platform.available ? (
                    <button className="btn btn-primary btn-sm" onClick={() => handleConnect(platform.platform)}>Connect</button>
                  ) : (
                    <span className="badge badge-info">Coming Soon</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Quick Actions */}
        <section className={styles.section}>
          <h2 className={styles.sectionTitle}>Quick Actions</h2>
          <div className={styles.quickActions}>
            {[
              { label: 'New Chat', icon: '💬', action: () => router.push('/chat') },
              { label: 'Create Issue', icon: '🐛', action: () => router.push('/chat?prompt=Create a GitHub issue') },
              { label: 'List Repos', icon: '📦', action: () => router.push('/chat?prompt=Show my GitHub repositories') },
              { label: 'Create PR', icon: '🔀', action: () => router.push('/chat?prompt=Create a pull request') },
            ].map((action, i) => (
              <button
                key={action.label}
                className={`${styles.quickActionBtn} glass-card`}
                onClick={action.action}
                style={{ animationDelay: `${i * 60}ms` }}
              >
                <span className={styles.quickActionIcon}>{action.icon}</span>
                <span>{action.label}</span>
              </button>
            ))}
          </div>
        </section>

        {/* Recent Conversations */}
        <section className={styles.section}>
          <h2 className={styles.sectionTitle}>Recent Conversations</h2>
          {conversations.length === 0 ? (
            <div className={styles.emptyState}>
              <p>No conversations yet.</p>
              <button className="btn btn-primary" onClick={() => router.push('/chat')}>
                Start a conversation
              </button>
            </div>
          ) : (
            <div className={styles.conversationList}>
              {conversations.slice(0, 5).map((conv, i) => (
                <button
                  key={conv.id}
                  className={`${styles.conversationItem} glass-card`}
                  onClick={() => router.push(`/chat?conversation=${conv.id}`)}
                  style={{ animationDelay: `${i * 60}ms` }}
                >
                  <div className={styles.convIcon}>
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
                    </svg>
                  </div>
                  <div className={styles.convInfo}>
                    <h4 className={styles.convTitle}>{conv.title}</h4>
                    {conv.last_message && (
                      <p className={styles.convPreview}>{conv.last_message.slice(0, 80)}...</p>
                    )}
                  </div>
                  <span className={styles.convTime}>
                    {new Date(conv.updated_at).toLocaleDateString()}
                  </span>
                </button>
              ))}
            </div>
          )}
        </section>
      </main>
    </div>
  );
}
