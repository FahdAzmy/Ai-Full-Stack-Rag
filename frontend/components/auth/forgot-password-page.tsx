'use client';

import React, { useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { AppDispatch, RootState } from '@/store/store';
import { forgotPassword, resetPassword } from '@/store/auth/auth-actions';
import { clearError, clearSuccess } from '@/store/auth/auth-slice';
import { useLanguage } from '@/lib/language-context';
import { validateEmail, validatePassword, validateVerificationCode, validatePasswordMatch, type ValidationErrors } from '@/lib/validation';
import { Loader2, ArrowRight, Mail, Lock, ArrowLeft, Stethoscope, ShieldCheck, Clock, Zap, AlertCircle, CheckCircle2 } from 'lucide-react';

interface ForgotPasswordPageProps {
  onSuccess?: () => void;
  onBackClick?: () => void;
}

export function ForgotPasswordPage({ onSuccess, onBackClick }: ForgotPasswordPageProps) {
  const { t, isRTL } = useLanguage();
  const dispatch = useDispatch<AppDispatch>();
  const { isLoading, error, successMessage } = useSelector((state: RootState) => state.auth);

  const [step, setStep] = useState<'email' | 'reset'>('email');
  const [email, setEmail] = useState('');
  const [code, setCode] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [validationErrors, setValidationErrors] = useState<ValidationErrors>({});

  useEffect(() => {
    dispatch(clearSuccess());
    return () => {
      dispatch(clearError());
      dispatch(clearSuccess());
    };
  }, [dispatch]);

  useEffect(() => {
    if (successMessage) {
      if (step === 'email' && successMessage === 'PASSWORD_RESET_CODE_SENT') {
        setStep('reset');
        dispatch(clearSuccess());
      } else if (step === 'reset' && successMessage === 'PASSWORD_RESET_SUCCESS' && onSuccess) {
        const timer = setTimeout(() => { onSuccess(); }, 1500);
        return () => clearTimeout(timer);
      }
    }
  }, [successMessage, step, onSuccess, dispatch]);

  const validateEmailStep = (): boolean => {
    const newErrors: ValidationErrors = {};
    const emailError = validateEmail(email);
    if (emailError) newErrors.email = emailError;
    setValidationErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const validateResetStep = (): boolean => {
    const newErrors: ValidationErrors = {};
    const codeError = validateVerificationCode(code);
    if (codeError) newErrors.code = codeError;
    const passwordError = validatePassword(newPassword);
    if (passwordError) newErrors.newPassword = passwordError;
    const matchError = validatePasswordMatch(newPassword, confirmPassword);
    if (matchError) newErrors.confirmPassword = matchError;
    setValidationErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleEmailSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!validateEmailStep()) return;
    dispatch(forgotPassword(email));
  };

  const handleResetSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!validateResetStep()) return;
    dispatch(resetPassword({ email, code, new_password: newPassword }));
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

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>, field: string) => {
    const value = e.target.value;
    if (field === 'email') setEmail(value);
    else if (field === 'newPassword') setNewPassword(value);
    else if (field === 'confirmPassword') setConfirmPassword(value);
    if (validationErrors[field]) {
      const newErrors = { ...validationErrors };
      delete newErrors[field];
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
        
        {/* Mobile Logo Logo */}
        <div className="flex items-center gap-2 mb-6 md:hidden">
          <div className="size-8 bg-primary text-primary-foreground flex items-center justify-center rounded-lg shadow-sm">
            <span className="material-symbols-outlined !text-2xl">auto_stories</span>
          </div>
          <span className="font-bold text-lg text-foreground">{t('scholarGpt') || 'ScholarGPT'}</span>
        </div>

        {/* Header */}
        <div className="mb-6">
          <div className="w-14 h-14 rounded-2xl bg-primary flex items-center justify-center mb-5 shadow-sm">
            <Lock className="w-7 h-7 text-primary-foreground" />
          </div>
          <h2 className="text-xl font-bold text-foreground mb-2">
            {step === 'email' ? t('forgotPasswordTitle') : t('resetPasswordTitle')}
          </h2>
          <p className="text-sm font-medium text-muted-foreground leading-relaxed">
            {step === 'email' ? t('forgotPasswordDescription') : t('resetPasswordDescription')}
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

        {/* ── Step 1: Email ── */}
        {step === 'email' ? (
          <form onSubmit={handleEmailSubmit} className="space-y-4">
            <div className="space-y-1.5">
              <label htmlFor="email" className="block text-sm font-medium text-foreground">{t('email')}</label>
              <div className="relative">
                <Mail className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <input
                  id="email"
                  type="email"
                  placeholder={t('emailPlaceholder')}
                  value={email}
                  onChange={(e) => handleInputChange(e, 'email')}
                  disabled={isLoading}
                  className={`w-full pl-10 pr-4 py-2.5 bg-background border ${validationErrors.email ? 'border-destructive focus:ring-destructive/20 focus:border-destructive' : 'border-input focus:ring-primary/20 focus:border-primary'} text-foreground rounded-xl focus:ring-4 outline-none transition-all placeholder:text-muted-foreground font-medium`}
                />
              </div>
              {validationErrors.email && (
                <p className="text-xs font-medium text-destructive mt-1.5">{t(validationErrors.email)}</p>
              )}
            </div>

            <button type="submit" disabled={isLoading} className="w-full bg-primary hover:bg-primary-light text-primary-foreground font-bold py-3 mt-4 rounded-xl shadow-md hover:shadow-lg transition-all flex items-center justify-center gap-2 active:scale-[0.98]">
              {isLoading ? (
                <><Loader2 className="w-5 h-5 animate-spin" /><span>{t('loading')}</span></>
              ) : (
                <><span>{t('forgotPasswordButton')}</span><ArrowRight className="w-4 h-4" /></>
              )}
            </button>

            <button type="button" onClick={onBackClick} disabled={isLoading} className="w-full bg-transparent hover:bg-muted text-foreground font-bold py-3 rounded-xl flex items-center justify-center gap-2 transition-all border border-border mt-3">
              <ArrowLeft className="w-4 h-4" />
              {t('backToLogin')}
            </button>
          </form>

        ) : (
          /* ── Step 2: Reset ── */
          <form onSubmit={handleResetSubmit} className="space-y-4">

            {/* Code */}
            <div className="space-y-1.5">
              <label htmlFor="code" className="block text-sm font-medium text-foreground">{t('verificationCode')}</label>
              <input
                id="code"
                type="text"
                placeholder={t('verificationCodePlaceholder')}
                value={code}
                onChange={handleCodeChange}
                disabled={isLoading}
                maxLength={6}
                className={`w-full py-2.5 bg-background border ${validationErrors.code ? 'border-destructive focus:ring-destructive/20 focus:border-destructive' : 'border-input focus:ring-primary/20 focus:border-primary'} text-foreground rounded-xl focus:ring-4 outline-none transition-all placeholder:text-muted-foreground font-mono text-center text-xl tracking-[0.5em] font-bold shadow-sm`}
              />
              {validationErrors.code && (
                <p className="text-xs font-medium text-destructive mt-1.5 text-center">{t(validationErrors.code)}</p>
              )}
            </div>

            {/* New Password */}
            <div className="space-y-1.5">
              <label htmlFor="newPassword" className="block text-sm font-medium text-foreground">{t('newPassword')}</label>
              <div className="relative">
                <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <input
                  id="newPassword"
                  type="password"
                  placeholder={t('newPasswordPlaceholder')}
                  value={newPassword}
                  onChange={(e) => handleInputChange(e, 'newPassword')}
                  disabled={isLoading}
                  className={`w-full pl-10 pr-4 py-2.5 bg-background border ${validationErrors.newPassword ? 'border-destructive focus:ring-destructive/20 focus:border-destructive' : 'border-input focus:ring-primary/20 focus:border-primary'} text-foreground rounded-xl focus:ring-4 outline-none transition-all placeholder:text-muted-foreground font-medium`}
                />
              </div>
              {validationErrors.newPassword && (
                <p className="text-xs font-medium text-destructive mt-1.5">{t(validationErrors.newPassword)}</p>
              )}
            </div>

            {/* Confirm Password */}
            <div className="space-y-1.5">
              <label htmlFor="confirmPassword" className="block text-sm font-medium text-foreground">{t('confirmPassword')}</label>
              <div className="relative">
                <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <input
                  id="confirmPassword"
                  type="password"
                  placeholder={t('confirmPasswordPlaceholder')}
                  value={confirmPassword}
                  onChange={(e) => handleInputChange(e, 'confirmPassword')}
                  disabled={isLoading}
                  className={`w-full pl-10 pr-4 py-2.5 bg-background border ${validationErrors.confirmPassword ? 'border-destructive focus:ring-destructive/20 focus:border-destructive' : 'border-input focus:ring-primary/20 focus:border-primary'} text-foreground rounded-xl focus:ring-4 outline-none transition-all placeholder:text-muted-foreground font-medium`}
                />
              </div>
              {validationErrors.confirmPassword && (
                <p className="text-xs font-medium text-destructive mt-1.5">{t(validationErrors.confirmPassword)}</p>
              )}
            </div>

            <button type="submit" disabled={isLoading} className="w-full bg-primary hover:bg-primary-light text-primary-foreground font-bold py-3 mt-4 rounded-xl shadow-md hover:shadow-lg transition-all flex items-center justify-center gap-2 active:scale-[0.98]">
              {isLoading ? (
                <><Loader2 className="w-5 h-5 animate-spin" /><span>{t('loading')}</span></>
              ) : (
                <><span>{t('resetPasswordButton')}</span><ArrowRight className="w-4 h-4" /></>
              )}
            </button>

            <button type="button" onClick={onBackClick} disabled={isLoading} className="w-full bg-transparent hover:bg-muted text-foreground font-bold py-3 rounded-xl flex items-center justify-center gap-2 transition-all border border-border mt-3">
              <ArrowLeft className="w-4 h-4" />
              {t('backToLogin')}
            </button>
          </form>
        )}
      </div>
    </>
  );
}
