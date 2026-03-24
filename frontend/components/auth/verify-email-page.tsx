'use client';

import React, { useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { AppDispatch, RootState } from '@/store/store';
import { verifyEmail, resendCode } from '@/store/auth/auth-actions';
import { clearError, clearSuccess, clearPendingEmail } from '@/store/auth/auth-slice';
import { useLanguage } from '@/lib/language-context';
import { validateVerificationCode, type ValidationErrors } from '@/lib/validation';
import { Mail, RefreshCw } from 'lucide-react';
import { AuthLogo, AuthAlert, AuthInput, AuthCard, AuthSubmit } from './auth-form-components';

interface VerifyEmailPageProps {
  onSuccess?: () => void;
  onBackClick?: () => void;
}

export function VerifyEmailPage({ onSuccess, onBackClick }: VerifyEmailPageProps) {
  const { t } = useLanguage();
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
      <AuthLogo variant="desktop" />

      <AuthCard>
        <div className="mb-6">
          <AuthLogo variant="mobile" />

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

        {error && <AuthAlert type="error" message={error} />}
        {successMessage && <AuthAlert type="success" message={successMessage} />}

        <form onSubmit={handleSubmit} className="space-y-5">
          {/* Code input */}
          <div className="space-y-1.5">
            <label htmlFor="code" className="block text-sm font-medium text-foreground">{t('verificationCode')}</label>
            <AuthInput
              id="code"
              type="text"
              placeholder="000000"
              value={code}
              onChange={handleCodeChange}
              disabled={isLoading}
              maxLength={6}
              codeStyle
              error={validationErrors.code}
            />
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
          <AuthSubmit loading={isLoading} disabled={code.length !== 6}>
            <span>{t('verifyButton')}</span>
          </AuthSubmit>

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
      </AuthCard>
    </>
  );
}
