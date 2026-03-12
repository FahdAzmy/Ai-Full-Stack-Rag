'use client';

import React, { useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { AppDispatch, RootState } from '@/store/store';
import { verifyEmail, resendCode } from '@/store/auth/auth-actions';
import { clearError, clearSuccess, clearPendingEmail } from '@/store/auth/auth-slice';
import { useLanguage } from '@/lib/language-context';
import { validateVerificationCode, type ValidationErrors } from '@/lib/validation';
import { Loader2, Mail, Stethoscope, ShieldCheck, Clock, Zap, AlertCircle, CheckCircle2, RefreshCw } from 'lucide-react';

interface VerifyEmailPageProps {
  onSuccess?: () => void;
  onBackClick?: () => void;
}

export function VerifyEmailPage({ onSuccess, onBackClick }: VerifyEmailPageProps) {
  const { t, isRTL } = useLanguage();
  const dispatch = useDispatch<AppDispatch>();
  const { isLoading, error, successMessage, pendingEmail } = useSelector((state: RootState) => state.auth);

  const [code, setCode] = useState('');
  const [validationErrors, setValidationErrors] = useState<ValidationErrors>({});
  const [canResend, setCanResend] = useState(false);
  const [timeLeft, setTimeLeft] = useState(60);

  useEffect(() => {
    dispatch(clearSuccess());
    return () => {
      dispatch(clearError());
      dispatch(clearSuccess());
    };
  }, [dispatch]);

  useEffect(() => {
    if (successMessage === 'EMAIL_VERIFIED' && onSuccess) {
      const timer = setTimeout(() => {
        dispatch(clearPendingEmail());
        onSuccess();
      }, 1500);
      return () => clearTimeout(timer);
    }
  }, [successMessage, onSuccess, dispatch]);

  useEffect(() => {
    if (timeLeft > 0 && !canResend) {
      const timer = setTimeout(() => setTimeLeft(timeLeft - 1), 1000);
      return () => clearTimeout(timer);
    } else if (timeLeft === 0) {
      setCanResend(true);
    }
  }, [timeLeft, canResend]);

  const validateForm = (): boolean => {
    const newErrors: ValidationErrors = {};
    const codeError = validateVerificationCode(code);
    if (codeError) newErrors.code = codeError;
    setValidationErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!validateForm()) return;
    if (!pendingEmail) { dispatch(clearError()); return; }
    dispatch(verifyEmail({ email: pendingEmail, code }));
  };

  const handleResendCode = () => {
    if (!pendingEmail) return;
    dispatch(resendCode(pendingEmail));
    setTimeLeft(60);
    setCanResend(false);
  };

  const handleCodeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value.replace(/\D/g, '').slice(0, 6);
    setCode(value);
    if (validationErrors.code) {
      const newErrors = { ...validationErrors };
      delete newErrors.code;
      setValidationErrors(newErrors);
    }
    if (error) dispatch(clearError());
  };

  return (
    <>
      <div className="w-full max-w-[420px] mb-8 text-center animate-in fade-in slide-in-from-bottom-4 duration-500 hidden md:block">
        <div className="flex items-center justify-center gap-2 mb-4">
          <div className="size-10 bg-primary text-primary-foreground flex items-center justify-center rounded-lg shadow-sm">
            <span className="material-symbols-outlined !text-3xl">auto_stories</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground">{t('scholarGpt') || 'ScholarGPT'}</h1>
        </div>
      </div>

      <div className="w-full max-w-[420px] mb-8 bg-card border border-border rounded-xl shadow-[0_10px_25px_-5px_rgba(6,76,57,0.05),0_8px_10px_-6px_rgba(6,76,57,0.05)] p-8 relative z-10 animate-in fade-in slide-in-from-bottom-8 duration-700">
        <div className="mb-6">
          {/* Mobile Logo */}
          <div className="flex items-center gap-2 mb-6 md:hidden">
            <div className="size-8 bg-primary text-primary-foreground flex items-center justify-center rounded-lg shadow-sm">
              <span className="material-symbols-outlined !text-2xl">auto_stories</span>
            </div>
            <span className="font-bold text-lg text-foreground">{t('scholarGpt') || 'ScholarGPT'}</span>
          </div>

          {/* Mail icon */}
          <div className="w-14 h-14 rounded-2xl bg-primary flex items-center justify-center mb-5 shadow-sm">
            <Mail className="w-7 h-7 text-primary-foreground" />
          </div>

          <h2 className="text-xl font-bold text-foreground mb-2">{t('verifyEmailTitle')}</h2>
          <p className="text-sm font-medium text-muted-foreground leading-relaxed">
            {t('verifyEmailDescription')}
            {pendingEmail && (
              <span className="block mt-1 font-bold text-foreground">{pendingEmail}</span>
            )}
          </p>
        </div>

        {/* Alerts */}
        {error && (
          <div className="mb-6 p-4 rounded-xl bg-destructive/10 border border-destructive/20 flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-destructive flex-shrink-0 mt-0.5" />
            <p className="text-sm font-medium text-destructive">{t(error)}</p>
          </div>
        )}
        {successMessage && (
          <div className="mb-6 p-4 rounded-xl bg-primary/10 border border-primary/20 flex items-start gap-3">
            <CheckCircle2 className="w-5 h-5 text-primary flex-shrink-0 mt-0.5" />
            <p className="text-sm font-medium text-primary">{t(successMessage)}</p>
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-5">

          {/* Code input */}
          <div className="space-y-1.5">
            <label htmlFor="code" className="block text-sm font-medium text-foreground">{t('verificationCode')}</label>
            <input
              id="code"
              type="text"
              placeholder="000000"
              value={code}
              onChange={handleCodeChange}
              disabled={isLoading}
              maxLength={6}
              className={`w-full py-3 bg-background border ${validationErrors.code ? 'border-destructive focus:ring-destructive/20 focus:border-destructive' : 'border-input focus:ring-primary/20 focus:border-primary'} text-foreground rounded-xl focus:ring-4 outline-none transition-all placeholder:text-muted-foreground font-mono text-center text-2xl tracking-[0.5em] font-bold shadow-sm`}
            />
            {validationErrors.code && (
              <p className="text-xs font-medium text-destructive text-center mt-1.5">{t(validationErrors.code)}</p>
            )}
          </div>

          {/* Resend */}
          <div className="text-center">
            <button
              type="button"
              onClick={handleResendCode}
              disabled={!canResend || isLoading}
              className={`inline-flex items-center gap-1.5 text-sm font-bold transition-colors ${
                canResend
                  ? 'text-primary hover:text-primary-light cursor-pointer hover:underline'
                  : 'text-muted-foreground cursor-not-allowed opacity-60'
              }`}
            >
              <RefreshCw className="w-3.5 h-3.5" />
              {t('resendCode')}
              {!canResend && <span className="opacity-80 ml-1">({timeLeft}s)</span>}
            </button>
          </div>

          {/* Submit */}
          <button
            type="submit"
            disabled={isLoading || code.length !== 6}
            className="w-full bg-primary hover:bg-primary-light text-primary-foreground font-bold py-3 mt-2 rounded-xl shadow-md hover:shadow-lg transition-all flex items-center justify-center gap-2 active:scale-[0.98] disabled:opacity-70 disabled:cursor-not-allowed"
          >
            {isLoading ? (
              <><Loader2 className="w-5 h-5 animate-spin" /><span>{t('loading')}</span></>
            ) : (
              <span>{t('verifyButton')}</span>
            )}
          </button>

          {/* Back */}
          <button
            type="button"
            onClick={onBackClick}
            disabled={isLoading}
            className="w-full bg-transparent hover:bg-muted text-foreground font-bold py-3 rounded-xl transition-all border border-border mt-3"
          >
            {t('backToLogin')}
          </button>
        </form>
      </div>
    </>
  );
}
