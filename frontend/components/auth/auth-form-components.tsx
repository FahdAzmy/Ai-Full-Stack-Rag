'use client';

import React from 'react';
import { useLanguage } from '@/lib/language-context';
import { AlertCircle, CheckCircle2 } from 'lucide-react';

// ── Auth Logo ───────────────────────────────────────────────────────────────

interface AuthLogoProps {
  /** 'desktop' shows full centered block (hidden on mobile), 'mobile' shows inline (hidden on desktop) */
  variant: 'desktop' | 'mobile';
}

export function AuthLogo({ variant }: AuthLogoProps) {
  const { t } = useLanguage();

  if (variant === 'desktop') {
    return (
      <div className="w-full max-w-[420px] mb-8 text-center animate-in fade-in slide-in-from-bottom-4 duration-500 hidden md:block">
        <div className="flex items-center justify-center gap-2 mb-4">
          <div className="size-10 bg-primary text-primary-foreground flex items-center justify-center rounded-lg shadow-sm">
            <span className="material-symbols-outlined !text-3xl">auto_stories</span>
          </div>
          <span className="font-bold text-xl tracking-tight text-primary">
            {t('scholarGpt') || 'AskAnyDoc'}
          </span>
        </div>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-2 mb-6 md:hidden">
      <div className="size-8 bg-primary text-primary-foreground flex items-center justify-center rounded-lg shadow-sm">
        <span className="material-symbols-outlined !text-2xl">auto_stories</span>
      </div>
      <span className="font-bold text-lg text-foreground">
        {t('scholarGpt') || 'AskAnyDoc'}
      </span>
    </div>
  );
}

// ── Auth Alert ──────────────────────────────────────────────────────────────

interface AuthAlertProps {
  type: 'error' | 'success';
  message: string;
}

export function AuthAlert({ type, message }: AuthAlertProps) {
  const { t } = useLanguage();

  if (type === 'error') {
    return (
      <div className="mb-6 p-4 rounded-xl bg-destructive/10 border border-destructive/20 flex items-start gap-3">
        <AlertCircle className="w-5 h-5 text-destructive flex-shrink-0 mt-0.5" />
        <p className="text-sm font-medium text-destructive">{t(message)}</p>
      </div>
    );
  }

  return (
    <div className="mb-6 p-4 rounded-xl bg-primary/10 border border-primary/20 flex items-start gap-3">
      <CheckCircle2 className="w-5 h-5 text-primary flex-shrink-0 mt-0.5" />
      <p className="text-sm font-medium text-primary">{t(message)}</p>
    </div>
  );
}

// ── Auth Input ──────────────────────────────────────────────────────────────

interface AuthInputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  icon?: React.ReactNode;
  error?: string;
  /** If true, centers text and uses monospaced font (for verification codes) */
  codeStyle?: boolean;
}

export const AuthInput = React.forwardRef<HTMLInputElement, AuthInputProps>(
  ({ icon, error, codeStyle, className, ...props }, ref) => {
    const { t } = useLanguage();

    const baseClasses = `w-full py-2.5 bg-background border text-foreground rounded-xl focus:ring-4 outline-none transition-all placeholder:text-muted-foreground font-medium`;
    const errorClasses = error
      ? 'border-destructive focus:ring-destructive/20 focus:border-destructive'
      : 'border-input focus:ring-primary/20 focus:border-primary';
    const codeClasses = codeStyle
      ? 'font-mono text-center text-xl tracking-[0.5em] font-bold shadow-sm'
      : '';
    const paddingClasses = icon ? 'pl-10 pr-4' : 'px-4';

    return (
      <div className="space-y-1.5">
        <div className="relative">
          {icon && (
            <div className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground">
              {icon}
            </div>
          )}
          <input
            ref={ref}
            className={`${baseClasses} ${errorClasses} ${codeClasses} ${paddingClasses} ${className || ''}`}
            {...props}
          />
        </div>
        {error && (
          <p className="text-xs font-medium text-destructive mt-1.5">{t(error)}</p>
        )}
      </div>
    );
  },
);

AuthInput.displayName = 'AuthInput';

// ── Auth Card ───────────────────────────────────────────────────────────────

interface AuthCardProps {
  children: React.ReactNode;
}

export function AuthCard({ children }: AuthCardProps) {
  return (
    <div className="w-full max-w-[420px] mb-8 bg-card border border-border rounded-xl shadow-[0_10px_25px_-5px_rgba(6,76,57,0.05),0_8px_10px_-6px_rgba(6,76,57,0.05)] p-8 relative z-10 animate-in fade-in slide-in-from-bottom-8 duration-700">
      {children}
    </div>
  );
}

// ── Auth Submit Button ──────────────────────────────────────────────────────

interface AuthSubmitProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  loading?: boolean;
  children: React.ReactNode;
}

export function AuthSubmit({ loading, children, className, ...props }: AuthSubmitProps) {
  const { t } = useLanguage();

  return (
    <button
      type="submit"
      disabled={loading || props.disabled}
      className={`w-full bg-primary hover:bg-primary-light text-primary-foreground font-bold py-3 mt-2 rounded-xl shadow-md hover:shadow-lg transition-all flex items-center justify-center gap-2 active:scale-[0.98] disabled:opacity-70 disabled:cursor-not-allowed ${className || ''}`}
      {...props}
    >
      {loading ? (
        <>
          <span className="material-symbols-outlined text-xl animate-spin">progress_activity</span>
          <span>{t('loading')}</span>
        </>
      ) : (
        children
      )}
    </button>
  );
}
