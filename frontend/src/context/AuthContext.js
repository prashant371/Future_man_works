'use client';

/**
 * Auth Context
 *
 * Provides authentication state across the entire app.
 * Handles login, register, logout, and session persistence.
 */

import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import api from '@/services/api';

const AuthContext = createContext(null);

// Routes that don't require authentication
const PUBLIC_ROUTES = ['/login', '/register'];

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();
  const pathname = usePathname();

  /**
   * Check for existing session on mount.
   */
  const checkAuth = useCallback(async () => {
    const token = api.getToken();
    if (!token) {
      setLoading(false);
      if (!PUBLIC_ROUTES.includes(pathname)) {
        router.push('/login');
      }
      return;
    }

    try {
      const userData = await api.getMe();
      setUser(userData);
    } catch {
      api.clearTokens();
      if (!PUBLIC_ROUTES.includes(pathname)) {
        router.push('/login');
      }
    } finally {
      setLoading(false);
    }
  }, [pathname, router]);

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  /**
   * Register a new user.
   */
  const register = async (email, name, password) => {
    await api.register(email, name, password);
    const userData = await api.getMe();
    setUser(userData);
    router.push('/dashboard');
  };

  /**
   * Log in an existing user.
   */
  const login = async (email, password) => {
    await api.login(email, password);
    const userData = await api.getMe();
    setUser(userData);
    router.push('/dashboard');
  };

  /**
   * Log out the current user.
   */
  const logout = async () => {
    await api.logout();
    setUser(null);
    router.push('/login');
  };

  const value = {
    user,
    loading,
    login,
    register,
    logout,
    isAuthenticated: !!user,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

export default AuthContext;
