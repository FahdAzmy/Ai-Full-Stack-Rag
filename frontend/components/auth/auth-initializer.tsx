'use client';

import { useEffect, useRef } from 'react';
import { useDispatch } from 'react-redux';
import { AppDispatch } from '@/store/store';
import { refreshToken } from '@/store/auth/auth-actions';

/**
 * AuthInitializer — runs once when the app mounts.
 * Dispatches refreshToken which:
 *   1. Calls POST /refresh (sends refresh_token cookie)
 *   2. Saves the new access token in memory
 *   3. Calls GET /profile to fetch user data
 *   4. Stores the user in Redux store
 *
 * If the refresh fails (no cookie, expired, etc.), it marks
 * isInitialized = true so the AuthGuard can redirect to login.
 */
export function AuthInitializer({ children }: { children: React.ReactNode }) {
  const dispatch = useDispatch<AppDispatch>();
  const initialized = useRef(false);

  useEffect(() => {
    if (!initialized.current) {
      initialized.current = true;
      dispatch(refreshToken());
    }
  }, [dispatch]);

  return <>{children}</>;
}
