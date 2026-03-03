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
    <div className={`auth-layout ${isRTL ? 'rtl' : 'ltr'}`}>

      {/* ── Left Branding Panel ── */}
      <div className="auth-panel-left">
        <div className="relative z-10">
          <div className="flex items-center gap-3 mb-16">
            <div className="w-10 h-10 rounded-xl bg-white/20 flex items-center justify-center">
              <Stethoscope className="w-6 h-6 text-white" />
            </div>
            <span className="text-white font-bold text-xl tracking-tight">{t('brandName')}</span>
          </div>

          <h1 className="text-4xl font-bold text-white leading-tight mb-4">
            {t('loginHeadline')}
          </h1>
          <p className="text-teal-100 text-base leading-relaxed mb-12">
            {t('verifyEmailSubheadline')}
          </p>

          <div className="space-y-5">
            {[
              { icon: <Zap className="w-4 h-4 text-white" />, title: t('featureInstantTitle'), desc: t('featureInstantDesc') },
              { icon: <ShieldCheck className="w-4 h-4 text-white" />, title: t('featureEvidenceTitle'), desc: t('featureEvidenceDesc') },
              { icon: <Clock className="w-4 h-4 text-white" />, title: t('featureGuidanceTitle'), desc: t('featureGuidanceDesc') },
            ].map((f, i) => (
              <div key={i} className="auth-feature-item">
                <div className="auth-feature-icon">{f.icon}</div>
                <div>
                  <p className="text-white font-semibold text-sm">{f.title}</p>
                  <p className="text-teal-200 text-xs mt-0.5">{f.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        <p className="relative z-10 text-teal-200 text-xs">
          {t('copyright')}
        </p>
      </div>

      {/* ── Right Form Panel ── */}
      <div className="auth-panel-right">
        <div className="auth-form-card">

          {/* Header */}
          <div className="mb-8">
            <div className="flex items-center gap-2 mb-8 lg:hidden">
              <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: 'linear-gradient(135deg,#0d9488,#0f766e)' }}>
                <Stethoscope className="w-4 h-4 text-white" />
              </div>
              <span className="font-bold text-base text-foreground">{t('brandName')}</span>
            </div>

            {/* Mail icon */}
            <div className="w-14 h-14 rounded-2xl flex items-center justify-center mb-5" style={{ background: 'linear-gradient(135deg,#0d9488,#0f766e)' }}>
              <Mail className="w-7 h-7 text-white" />
            </div>

            <h2 className="text-2xl font-bold text-foreground mb-1">{t('verifyEmailTitle')}</h2>
            <p className="text-muted-foreground text-sm">
              {t('verifyEmailDescription')}
              {pendingEmail && (
                <span className="block mt-1 font-medium text-foreground">{pendingEmail}</span>
              )}
            </p>
          </div>

          {/* Alerts */}
          {error && (
            <div className="med-alert-error">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              <span>{t(error)}</span>
            </div>
          )}
          {successMessage && (
            <div className="med-alert-success">
              <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
              <span>{t(successMessage)}</span>
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-5">

            {/* Code input */}
            <div className="space-y-1.5">
              <label className="text-sm font-medium text-foreground">{t('verificationCode')}</label>
              <input
                id="code"
                type="text"
                placeholder="000000"
                value={code}
                onChange={handleCodeChange}
                disabled={isLoading}
                maxLength={6}
                className={`med-input text-center text-2xl tracking-[0.5em] font-mono ${validationErrors.code ? 'med-input-error' : ''}`}
              />
              {validationErrors.code && (
                <p className="text-xs text-destructive text-center">{t(validationErrors.code)}</p>
              )}
            </div>

            {/* Resend */}
            <div className="text-center">
              <button
                type="button"
                onClick={handleResendCode}
                disabled={!canResend || isLoading}
                className={`inline-flex items-center gap-1.5 text-sm font-medium transition-colors ${
                  canResend
                    ? 'text-primary hover:text-primary/80 cursor-pointer'
                    : 'text-muted-foreground cursor-not-allowed'
                }`}
              >
                <RefreshCw className="w-3.5 h-3.5" />
                {t('resendCode')}
                {!canResend && <span className="opacity-60">({timeLeft}s)</span>}
              </button>
            </div>

            {/* Submit */}
            <button
              type="submit"
              disabled={isLoading || code.length !== 6}
              className="med-btn-primary"
            >
              {isLoading ? (
                <><Loader2 className="w-4 h-4 animate-spin" /><span>{t('loading')}</span></>
              ) : (
                <span>{t('verifyButton')}</span>
              )}
            </button>

            {/* Back */}
            <button
              type="button"
              onClick={onBackClick}
              disabled={isLoading}
              className="med-btn-ghost"
            >
              {t('backToLogin')}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
