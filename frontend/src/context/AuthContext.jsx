import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import {
  fetchMe,
  getAuthToken,
  loginAccount,
  logoutAccount,
  registerAccount,
  setAuthToken,
  subscribeMonthly,
  updateProfile,
} from '../api/auth';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const refreshUser = useCallback(async () => {
    const token = getAuthToken();
    if (!token) {
      setUser(null);
      setLoading(false);
      return null;
    }
    try {
      const data = await fetchMe();
      setUser(data.user);
      return data.user;
    } catch {
      setAuthToken(null);
      setUser(null);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refreshUser();
  }, [refreshUser]);

  const login = useCallback(async (email, password) => {
    const data = await loginAccount({ email, password });
    setAuthToken(data.token);
    setUser(data.user);
    return data.user;
  }, []);

  const register = useCallback(async (payload) => {
    const data = await registerAccount(payload);
    setAuthToken(data.token);
    setUser(data.user);
    return data.user;
  }, []);

  const logout = useCallback(async () => {
    try {
      await logoutAccount();
    } catch {
      /* session déjà expirée */
    }
    setAuthToken(null);
    setUser(null);
  }, []);

  const saveProfile = useCallback(async (payload) => {
    const data = await updateProfile(payload);
    setUser(data.user);
    return data.user;
  }, []);

  const subscribe = useCallback(async () => {
    const data = await subscribeMonthly();
    setUser(data.user);
    return data.user;
  }, []);

  const value = useMemo(
    () => ({
      user,
      loading,
      isAuthenticated: Boolean(user),
      hasPlatformAccess: Boolean(user?.access?.has_access),
      login,
      register,
      logout,
      refreshUser,
      saveProfile,
      subscribe,
    }),
    [user, loading, login, register, logout, refreshUser, saveProfile, subscribe]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error('useAuth doit être utilisé dans AuthProvider');
  }
  return ctx;
}
