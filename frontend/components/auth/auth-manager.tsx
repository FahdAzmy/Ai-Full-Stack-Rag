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
  const [pendingEmail, setPendingEmail] = useState<string>('');
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
    <div className={`min-h-screen bg-gradient-to-br from-background via-background to-muted/30 relative overflow-hidden transition-all duration-300`}>
      {/* Background decoration */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className={`absolute top-0 ${isRTL ? 'right-1/4' : 'left-1/4'} w-96 h-96 bg-primary/5 rounded-full blur-3xl`} />
        <div className={`absolute bottom-0 ${isRTL ? 'left-1/4' : 'right-1/4'} w-96 h-96 bg-accent/5 rounded-full blur-3xl`} />
      </div>

      {/* Switchers - Language and Theme */}
      <div className={`absolute top-4 ${isRTL ? 'left-4' : 'right-4'} z-50 transition-all duration-300 flex gap-2`}>
        <ThemeSwitcher />
        <LanguageSwitcher />
      </div>

      {/* Main Content */}
      <div className="relative z-10">
        {renderPage()}
      </div>
    </div>
  );
}
