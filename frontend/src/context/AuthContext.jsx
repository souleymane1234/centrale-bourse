import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import {
  fetchMe,
  fetchPublicConfig,
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
  const [paymentsEnabled, setPaymentsEnabled] = useState(false);

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
      setPaymentsEnabled(Boolean(data.user?.payments_enabled));
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
    let cancelled = false;

    async function bootstrap() {
      try {
        const config = await fetchPublicConfig();
        if (!cancelled) {
          setPaymentsEnabled(Boolean(config.payments_enabled));
        }
      } catch {
        if (!cancelled) {
          setPaymentsEnabled(false);
        }
      }
      await refreshUser();
    }

    bootstrap();
    return () => {
      cancelled = true;
    };
  }, [refreshUser]);

  const login = useCallback(async (email, password) => {
    const data = await loginAccount({ email, password });
    setAuthToken(data.token);
    setUser(data.user);
    setPaymentsEnabled(Boolean(data.user?.payments_enabled));
    return data.user;
  }, []);

  const register = useCallback(async (payload) => {
    const data = await registerAccount(payload);
    setAuthToken(data.token);
    setUser(data.user);
    setPaymentsEnabled(Boolean(data.user?.payments_enabled));
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
    setPaymentsEnabled(Boolean(data.user?.payments_enabled));
    return data.user;
  }, []);

  const subscribe = useCallback(async () => {
    const data = await subscribeMonthly();
    setUser(data.user);
    setPaymentsEnabled(Boolean(data.user?.payments_enabled));
    return data.user;
  }, []);

  const hasPlatformAccess = paymentsEnabled
    ? Boolean(user?.access?.has_access)
    : Boolean(user);

  const value = useMemo(
    () => ({
      user,
      loading,
      paymentsEnabled,
      isAuthenticated: Boolean(user),
      hasPlatformAccess,
      login,
      register,
      logout,
      refreshUser,
      saveProfile,
      subscribe,
    }),
    [
      user,
      loading,
      paymentsEnabled,
      hasPlatformAccess,
      login,
      register,
      logout,
      refreshUser,
      saveProfile,
      subscribe,
    ]
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
