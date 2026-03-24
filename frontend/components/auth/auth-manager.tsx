'use client';

import { useState, useEffect } from 'react';
import { useSelector } from 'react-redux';
import { useRouter } from 'next/navigation';
import { RootState } from '@/store/store';
import { useLanguage } from '@/lib/language-context';
import { LanguageSwitcher } from '@/components/language-switcher';
import { ThemeSwitcher } from '@/components/theme-switcher';
import { LoginPage } from './login-page';
import { SignUpPage } from './signup-page';
import { VerifyEmailPage } from './verify-email-page';
import { ForgotPasswordPage } from './forgot-password-page';
import { Loader2 } from 'lucide-react';

type AuthPage = 'login' | 'signup' | 'verify-email' | 'forgot-password';

export function AuthManager() {
  const [currentPage, setCurrentPage] = useState<AuthPage>('login');
  const { isRTL } = useLanguage();
  const { isAuthenticated, isInitialized } = useSelector((state: RootState) => state.auth);
  const router = useRouter();

  // If already authenticated, redirect to chat
  useEffect(() => {
    if (isInitialized && isAuthenticated) {
      router.replace('/chat');
    }
  }, [isAuthenticated, isInitialized, router]);

  // Show loading while checking session
  if (!isInitialized) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-white dark:bg-gray-950">
        <div className="flex flex-col items-center gap-4">
          <div
            className="size-12 rounded-xl flex items-center justify-center text-white shadow-lg"
            style={{ background: 'linear-gradient(135deg, #0d9488, #0f766e)' }}
          >
            <Loader2 className="w-6 h-6 animate-spin" />
          </div>
          <p className="text-sm text-muted-foreground font-medium">Loading...</p>
        </div>
      </div>
    );
  }

  const renderPage = () => {
    switch (currentPage) {
      case 'login':
        return (
          <LoginPage
            onSignUpClick={() => setCurrentPage('signup')}
            onForgotPasswordClick={() => setCurrentPage('forgot-password')}
          />
        );
      case 'signup':
        return (
          <SignUpPage
            onSuccess={() => setCurrentPage('verify-email')}
            onLoginClick={() => setCurrentPage('login')}
          />
        );
      case 'verify-email':
        return (
          <VerifyEmailPage
            onSuccess={() => setCurrentPage('login')}
            onBackClick={() => setCurrentPage('login')}
          />
        );
      case 'forgot-password':
        return (
          <ForgotPasswordPage
            onSuccess={() => setCurrentPage('login')}
            onBackClick={() => setCurrentPage('login')}
          />
        );
      default:
        return null;
    }
  };

  return (
    <div className={`flex-1 flex flex-col items-center justify-center p-6 bg-transparent transition-all duration-300 ${isRTL ? 'rtl' : 'ltr'}`}>
      <div className="w-full relative z-10 flex flex-col items-center">
        {renderPage()}
      </div>
    </div>
  );
}
