'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import api from '@/services/api';
import styles from '../dashboard/dashboard.module.css';

export default function TasksPage() {
  const { user, loading: authLoading, logout } = useAuth();
  const router = useRouter();
  const [tasks, setTasks] = useState([]);
  const [loadingTasks, setLoadingTasks] = useState(true);

  useEffect(() => {
    if (!authLoading && !user) {
      router.push('/login');
      return;
    }
    if (user) {
      loadTasks();
    }
  }, [user, authLoading]);

  const loadTasks = async () => {
    try {
      const data = await api.getTasks(50, 0);
      setTasks(data);
    } catch (err) {
      console.error('Failed to load tasks:', err);
    } finally {
      setLoadingTasks(false);
    }
  };

  if (authLoading || !user) {
    return (
      <div className={styles.loadingScreen}>
        <div className="spinner spinner-lg" />
      </div>
    );
  }

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
          <span className={styles.headerTitle}>Activity History</span>
        </div>
        <div className={styles.headerRight}>
          <button className="btn btn-ghost btn-sm" onClick={() => router.push('/dashboard')}>
            Dashboard
          </button>
          <button className="btn btn-ghost btn-sm" onClick={() => router.push('/chat')}>
            Chat
          </button>
        </div>
      </header>

      {/* Main Content */}
      <main className={styles.main}>
        <section className={styles.section}>
          <h2 className={styles.sectionTitle}>Task Execution Log</h2>
          
          {loadingTasks ? (
            <div className="spinner" />
          ) : tasks.length === 0 ? (
            <div className={styles.emptyState}>
              <p>No activity recorded yet.</p>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              {tasks.map((task) => (
                <div key={task.id} className="glass-card" style={{ padding: '16px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                    <h3 style={{ fontSize: '1rem', color: 'var(--text-primary)' }}>{task.goal || 'Tool Execution'}</h3>
                    <span className={`badge ${task.status === 'completed' ? 'badge-success' : task.status === 'failed' ? 'badge-error' : 'badge-warning'}`}>
                      {task.status}
                    </span>
                  </div>
                  <div style={{ fontSize: '0.8125rem', color: 'var(--text-tertiary)', display: 'flex', gap: '16px' }}>
                    <span>ID: {task.id.slice(0, 8)}...</span>
                    <span>Created: {new Date(task.created_at).toLocaleString()}</span>
                    {task.completed_at && <span>Completed: {new Date(task.completed_at).toLocaleString()}</span>}
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>
      </main>
    </div>
  );
}
