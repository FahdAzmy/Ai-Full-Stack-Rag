'use client';

import { useEffect } from 'react';
import { useSelector } from 'react-redux';
import { useRouter } from 'next/navigation';
import { RootState } from '@/store/store';
import { Loader2 } from 'lucide-react';

interface AuthGuardProps {
  children: React.ReactNode;
}

export function AuthGuard({ children }: AuthGuardProps) {
  const router = useRouter();
  const { isAuthenticated, isInitialized } = useSelector((state: RootState) => state.auth);

  useEffect(() => {
    // Only redirect AFTER the refresh attempt has completed
    if (isInitialized && !isAuthenticated) {
      router.replace('/');
    }
  }, [isAuthenticated, isInitialized, router]);

  // Show loading spinner while the refresh attempt is in progress
  if (!isInitialized || !isAuthenticated) {
    return (
      <div
        className="min-h-screen flex items-center justify-center bg-white dark:bg-gray-950"
        role="status"
        aria-label="Verifying access"
      >
        <div className="flex flex-col items-center gap-4">
          <div
            className="size-12 rounded-xl flex items-center justify-center text-white shadow-lg"
            style={{ background: 'linear-gradient(135deg, #0d9488, #0f766e)' }}
          >
            <Loader2 className="w-6 h-6 animate-spin" aria-hidden="true" />
          </div>
          <p className="text-sm text-muted-foreground font-medium">Verifying access...</p>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}
