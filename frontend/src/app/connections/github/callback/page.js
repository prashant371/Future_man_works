'use client';

import { useEffect, useState, useRef } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import api from '@/services/api';

export default function GitHubCallbackPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { user, loading: authLoading } = useAuth();
  
  const [status, setStatus] = useState('Connecting to GitHub...');
  const [error, setError] = useState('');
  const handled = useRef(false);

  useEffect(() => {
    if (authLoading) return;
    if (!user) {
      router.push('/login');
      return;
    }

    const code = searchParams.get('code');
    const state = searchParams.get('state');
    
    if (!code || !state) {
      setError('Missing authorization code or state.');
      return;
    }

    if (handled.current) return;
    handled.current = true;

    const handleCallback = async () => {
      try {
        await api.request('POST', '/api/connections/github/callback', { code, state });
        setStatus('Successfully connected to GitHub! Redirecting...');
        setTimeout(() => {
          router.push('/dashboard');
        }, 1500);
      } catch (err) {
        setError(err.message || 'Failed to complete GitHub connection.');
      }
    };

    handleCallback();
  }, [user, authLoading, searchParams, router]);

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      minHeight: '100vh',
      gap: '20px'
    }}>
      {error ? (
        <div style={{ color: 'var(--accent-danger)', textAlign: 'center' }}>
          <h2>Connection Failed</h2>
          <p>{error}</p>
          <button className="btn btn-primary" onClick={() => router.push('/dashboard')} style={{ marginTop: '20px' }}>
            Return to Dashboard
          </button>
        </div>
      ) : (
        <>
          <div className="spinner spinner-lg" />
          <h2>{status}</h2>
        </>
      )}
    </div>
  );
}
