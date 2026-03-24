'use client';

import React, { useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { AppDispatch, RootState } from '@/store/store';
import { forgotPassword, resetPassword } from '@/store/auth/auth-actions';
import { clearError, clearSuccess } from '@/store/auth/auth-slice';
import { useLanguage } from '@/lib/language-context';
import { validateEmail, validatePassword, validateVerificationCode, validatePasswordMatch, type ValidationErrors } from '@/lib/validation';
import { ArrowRight, Mail, Lock, ArrowLeft } from 'lucide-react';
import { AuthLogo, AuthAlert, AuthInput, AuthCard, AuthSubmit } from './auth-form-components';

interface ForgotPasswordPageProps {
  onSuccess?: () => void;
  onBackClick?: () => void;
}

export function ForgotPasswordPage({ onSuccess, onBackClick }: ForgotPasswordPageProps) {
  const { t } = useLanguage();
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
      <AuthLogo variant="desktop" />

      <AuthCard>
        <AuthLogo variant="mobile" />

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

        {error && <AuthAlert type="error" message={error} />}
        {successMessage && <AuthAlert type="success" message={successMessage} />}

        {/* ── Step 1: Email ── */}
        {step === 'email' ? (
          <form onSubmit={handleEmailSubmit} className="space-y-4">
            <div className="space-y-1.5">
              <label htmlFor="email" className="block text-sm font-medium text-foreground">{t('email')}</label>
              <AuthInput
                id="email"
                type="email"
                placeholder={t('emailPlaceholder')}
                value={email}
                onChange={(e) => handleInputChange(e, 'email')}
                disabled={isLoading}
                icon={<Mail className="w-4 h-4" />}
                error={validationErrors.email}
              />
            </div>

            <AuthSubmit loading={isLoading} className="mt-4">
              <span>{t('forgotPasswordButton')}</span>
              <ArrowRight className="w-4 h-4" />
            </AuthSubmit>

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
              <AuthInput
                id="code"
                type="text"
                placeholder={t('verificationCodePlaceholder')}
                value={code}
                onChange={handleCodeChange}
                disabled={isLoading}
                maxLength={6}
                codeStyle
                error={validationErrors.code}
              />
            </div>

            {/* New Password */}
            <div className="space-y-1.5">
              <label htmlFor="newPassword" className="block text-sm font-medium text-foreground">{t('newPassword')}</label>
              <AuthInput
                id="newPassword"
                type="password"
                placeholder={t('newPasswordPlaceholder')}
                value={newPassword}
                onChange={(e) => handleInputChange(e, 'newPassword')}
                disabled={isLoading}
                icon={<Lock className="w-4 h-4" />}
                error={validationErrors.newPassword}
              />
            </div>

            {/* Confirm Password */}
            <div className="space-y-1.5">
              <label htmlFor="confirmPassword" className="block text-sm font-medium text-foreground">{t('confirmPassword')}</label>
              <AuthInput
                id="confirmPassword"
                type="password"
                placeholder={t('confirmPasswordPlaceholder')}
                value={confirmPassword}
                onChange={(e) => handleInputChange(e, 'confirmPassword')}
                disabled={isLoading}
                icon={<Lock className="w-4 h-4" />}
                error={validationErrors.confirmPassword}
              />
            </div>

            <AuthSubmit loading={isLoading} className="mt-4">
              <span>{t('resetPasswordButton')}</span>
              <ArrowRight className="w-4 h-4" />
            </AuthSubmit>

            <button type="button" onClick={onBackClick} disabled={isLoading} className="w-full bg-transparent hover:bg-muted text-foreground font-bold py-3 rounded-xl flex items-center justify-center gap-2 transition-all border border-border mt-3">
              <ArrowLeft className="w-4 h-4" />
              {t('backToLogin')}
            </button>
          </form>
        )}
      </AuthCard>
    </>
  );
}
