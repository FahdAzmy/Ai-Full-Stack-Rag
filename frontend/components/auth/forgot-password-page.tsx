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

  /* Shared left panel */
  const LeftPanel = () => (
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
          {t('forgotPasswordSubheadline')}
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
  );

  return (
    <div className={`auth-layout ${isRTL ? 'rtl' : 'ltr'}`}>
      <LeftPanel />

      {/* ── Right Form Panel ── */}
      <div className="auth-panel-right">
        <div className="auth-form-card">

          {/* Mobile logo */}
          <div className="flex items-center gap-2 mb-8 lg:hidden">
            <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: 'linear-gradient(135deg,#0d9488,#0f766e)' }}>
              <Stethoscope className="w-4 h-4 text-white" />
            </div>
            <span className="font-bold text-base text-foreground">{t('brandName')}</span>
          </div>

          {/* Icon + Title */}
          <div className="mb-7">
            <div className="w-14 h-14 rounded-2xl flex items-center justify-center mb-5" style={{ background: 'linear-gradient(135deg,#0d9488,#0f766e)' }}>
              <Lock className="w-7 h-7 text-white" />
            </div>
            <h2 className="text-2xl font-bold text-foreground mb-1">
              {step === 'email' ? t('forgotPasswordTitle') : t('resetPasswordTitle')}
            </h2>
            <p className="text-muted-foreground text-sm">
              {step === 'email' ? t('forgotPasswordDescription') : t('resetPasswordDescription')}
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

          {/* ── Step 1: Email ── */}
          {step === 'email' ? (
            <form onSubmit={handleEmailSubmit} className="space-y-4">
              <div className="space-y-1.5">
                <label className="text-sm font-medium text-foreground">{t('email')}</label>
                <div className="relative">
                  <Mail className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                  <input
                    type="email"
                    placeholder={t('emailPlaceholder')}
                    value={email}
                    onChange={(e) => handleInputChange(e, 'email')}
                    disabled={isLoading}
                    className={`med-input med-input-icon ${validationErrors.email ? 'med-input-error' : ''}`}
                  />
                </div>
                {validationErrors.email && (
                  <p className="text-xs text-destructive">{t(validationErrors.email)}</p>
                )}
              </div>

              <button type="submit" disabled={isLoading} className="med-btn-primary">
                {isLoading ? (
                  <><Loader2 className="w-4 h-4 animate-spin" /><span>{t('loading')}</span></>
                ) : (
                  <><span>{t('forgotPasswordButton')}</span><ArrowRight className="w-4 h-4" /></>
                )}
              </button>

              <button type="button" onClick={onBackClick} disabled={isLoading} className="med-btn-ghost">
                <ArrowLeft className="w-4 h-4" />
                {t('backToLogin')}
              </button>
            </form>

          ) : (
            /* ── Step 2: Reset ── */
            <form onSubmit={handleResetSubmit} className="space-y-4">

              {/* Code */}
              <div className="space-y-1.5">
                <label className="text-sm font-medium text-foreground">{t('verificationCode')}</label>
                <input
                  type="text"
                  placeholder={t('verificationCodePlaceholder')}
                  value={code}
                  onChange={handleCodeChange}
                  disabled={isLoading}
                  maxLength={6}
                  className={`med-input text-center text-xl tracking-[0.5em] font-mono ${validationErrors.code ? 'med-input-error' : ''}`}
                />
                {validationErrors.code && (
                  <p className="text-xs text-destructive text-center">{t(validationErrors.code)}</p>
                )}
              </div>

              {/* New Password */}
              <div className="space-y-1.5">
                <label className="text-sm font-medium text-foreground">{t('newPassword')}</label>
                <div className="relative">
                  <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                  <input
                    type="password"
                    placeholder={t('newPasswordPlaceholder')}
                    value={newPassword}
                    onChange={(e) => handleInputChange(e, 'newPassword')}
                    disabled={isLoading}
                    className={`med-input med-input-icon ${validationErrors.newPassword ? 'med-input-error' : ''}`}
                  />
                </div>
                {validationErrors.newPassword && (
                  <p className="text-xs text-destructive">{t(validationErrors.newPassword)}</p>
                )}
              </div>

              {/* Confirm Password */}
              <div className="space-y-1.5">
                <label className="text-sm font-medium text-foreground">{t('confirmPassword')}</label>
                <div className="relative">
                  <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                  <input
                    type="password"
                    placeholder={t('confirmPasswordPlaceholder')}
                    value={confirmPassword}
                    onChange={(e) => handleInputChange(e, 'confirmPassword')}
                    disabled={isLoading}
                    className={`med-input med-input-icon ${validationErrors.confirmPassword ? 'med-input-error' : ''}`}
                  />
                </div>
                {validationErrors.confirmPassword && (
                  <p className="text-xs text-destructive">{t(validationErrors.confirmPassword)}</p>
                )}
              </div>

              <button type="submit" disabled={isLoading} className="med-btn-primary">
                {isLoading ? (
                  <><Loader2 className="w-4 h-4 animate-spin" /><span>{t('loading')}</span></>
                ) : (
                  <><span>{t('resetPasswordButton')}</span><ArrowRight className="w-4 h-4" /></>
                )}
              </button>

              <button type="button" onClick={onBackClick} disabled={isLoading} className="med-btn-ghost">
                <ArrowLeft className="w-4 h-4" />
                {t('backToLogin')}
              </button>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}
