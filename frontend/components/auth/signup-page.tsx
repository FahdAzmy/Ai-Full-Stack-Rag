'use client';

import React, { useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { AppDispatch, RootState } from '@/store/store';
import { signup } from '@/store/auth/auth-actions';
import { clearError, setPendingEmail } from '@/store/auth/auth-slice';
import { useLanguage } from '@/lib/language-context';
import { validateEmail, validatePassword, validateFullName, validatePasswordMatch, type ValidationErrors } from '@/lib/validation';
import { Input } from '@/components/ui/input';
import { Checkbox } from '@/components/ui/checkbox';
import { Loader2, User, Mail, Lock, Stethoscope, ShieldCheck, Clock, Zap, AlertCircle, CheckCircle2 } from 'lucide-react';
import { PasswordStrengthIndicator } from '@/components/password-strength-indicator';

interface SignUpPageProps {
  onSuccess?: () => void;
  onLoginClick?: () => void;
}

export function SignUpPage({ onSuccess, onLoginClick }: SignUpPageProps) {
  const { t, isRTL } = useLanguage();
  const dispatch = useDispatch<AppDispatch>();
  const { isLoading, error, successMessage } = useSelector((state: RootState) => state.auth);

  const [formData, setFormData] = useState({
    fullName: '',
    email: '',
    password: '',
    confirmPassword: '',
  });
  const [validationErrors, setValidationErrors] = useState<ValidationErrors>({});
  const [agreeToTerms, setAgreeToTerms] = useState(false);

  useEffect(() => {
    return () => { dispatch(clearError()); };
  }, [dispatch]);

  useEffect(() => {
    if (successMessage && onSuccess) {
      const timer = setTimeout(() => { onSuccess(); }, 1500);
      return () => clearTimeout(timer);
    }
  }, [successMessage, onSuccess]);

  const validateForm = (): boolean => {
    const newErrors: ValidationErrors = {};
    const nameError = validateFullName(formData.fullName);
    if (nameError) newErrors.fullName = nameError;
    const emailError = validateEmail(formData.email);
    if (emailError) newErrors.email = emailError;
    const passwordError = validatePassword(formData.password);
    if (passwordError) newErrors.password = passwordError;
    const matchError = validatePasswordMatch(formData.password, formData.confirmPassword);
    if (matchError) newErrors.confirmPassword = matchError;
    if (!agreeToTerms) newErrors.terms = 'requiredField';
    setValidationErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    if (validationErrors[name]) {
      const newErrors = { ...validationErrors };
      delete newErrors[name];
      setValidationErrors(newErrors);
    }
    if (error) dispatch(clearError());
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!validateForm()) return;
    dispatch(setPendingEmail(formData.email));
    dispatch(signup({ name: formData.fullName, email: formData.email, password: formData.password }));
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
            {t('signupHeadline')}
          </h1>
          <p className="text-teal-100 text-base leading-relaxed mb-12">
            {t('signupSubheadline')}
          </p>

          <div className="space-y-5">
            {[
              { icon: <Zap className="w-4 h-4 text-white" />, title: t('featureVerifiedTitle'), desc: t('featureVerifiedDesc') },
              { icon: <ShieldCheck className="w-4 h-4 text-white" />, title: t('featureSecureTitle'), desc: t('featureSecureDesc') },
              { icon: <Clock className="w-4 h-4 text-white" />, title: t('featureRealtimeTitle'), desc: t('featureRealtimeDesc') },
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
          <div className="mb-7">
            <div className="flex items-center gap-2 mb-8 lg:hidden">
              <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: 'linear-gradient(135deg,#0d9488,#0f766e)' }}>
                <Stethoscope className="w-4 h-4 text-white" />
              </div>
              <span className="font-bold text-base text-foreground">{t('brandName')}</span>
            </div>
            <h2 className="text-2xl font-bold text-foreground mb-1">{t('createAccountTitle')}</h2>
            <p className="text-muted-foreground text-sm">{t('createAccountSub')}</p>
          </div>

          {/* Alert */}
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
          <form onSubmit={handleSubmit} className="space-y-4">

            {/* Full Name */}
            <div className="space-y-1.5">
              <label className="text-sm font-medium text-foreground">{t('fullName')}</label>
              <div className="relative">
                <User className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <input
                  name="fullName"
                  type="text"
                  placeholder={t('fullNamePlaceholder')}
                  value={formData.fullName}
                  onChange={handleChange}
                  disabled={isLoading}
                  className={`med-input med-input-icon ${validationErrors.fullName ? 'med-input-error' : ''}`}
                />
              </div>
              {validationErrors.fullName && (
                <p className="text-xs text-destructive">{t(validationErrors.fullName)}</p>
              )}
            </div>

            {/* Email */}
            <div className="space-y-1.5">
              <label className="text-sm font-medium text-foreground">{t('email')}</label>
              <div className="relative">
                <Mail className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <input
                  name="email"
                  type="email"
                  placeholder={t('emailPlaceholder')}
                  value={formData.email}
                  onChange={handleChange}
                  disabled={isLoading}
                  className={`med-input med-input-icon ${validationErrors.email ? 'med-input-error' : ''}`}
                />
              </div>
              {validationErrors.email && (
                <p className="text-xs text-destructive">{t(validationErrors.email)}</p>
              )}
            </div>

            {/* Password */}
            <div className="space-y-1.5">
              <label className="text-sm font-medium text-foreground">{t('password')}</label>
              <div className="relative">
                <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <input
                  name="password"
                  type="password"
                  placeholder={t('passwordPlaceholder')}
                  value={formData.password}
                  onChange={handleChange}
                  disabled={isLoading}
                  className={`med-input med-input-icon ${validationErrors.password ? 'med-input-error' : ''}`}
                />
              </div>
              {formData.password && !validationErrors.password && (
                <div className="mt-1">
                  <PasswordStrengthIndicator password={formData.password} />
                </div>
              )}
              {validationErrors.password && (
                <p className="text-xs text-destructive">{t(validationErrors.password)}</p>
              )}
            </div>

            {/* Confirm Password */}
            <div className="space-y-1.5">
              <label className="text-sm font-medium text-foreground">{t('confirmPassword')}</label>
              <div className="relative">
                <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <input
                  name="confirmPassword"
                  type="password"
                  placeholder={t('confirmPasswordPlaceholder')}
                  value={formData.confirmPassword}
                  onChange={handleChange}
                  disabled={isLoading}
                  className={`med-input med-input-icon ${validationErrors.confirmPassword ? 'med-input-error' : ''}`}
                />
              </div>
              {validationErrors.confirmPassword && (
                <p className="text-xs text-destructive">{t(validationErrors.confirmPassword)}</p>
              )}
            </div>

            {/* Terms */}
            <div className={`flex items-start gap-3 p-3 rounded-lg border ${validationErrors.terms ? 'border-destructive/30 bg-destructive/5' : 'border-transparent bg-gray-50'}`}>
              <Checkbox
                id="terms"
                checked={agreeToTerms}
                onCheckedChange={(checked) => {
                  setAgreeToTerms(checked as boolean);
                  if (validationErrors.terms) {
                    const newErrors = { ...validationErrors };
                    delete newErrors.terms;
                    setValidationErrors(newErrors);
                  }
                }}
                disabled={isLoading}
                className="mt-0.5 data-[state=checked]:bg-primary data-[state=checked]:border-primary"
              />
              <label htmlFor="terms" className="text-xs text-muted-foreground leading-relaxed cursor-pointer select-none">
                {t('agreeTerms')}{' '}
                <span className="text-primary font-semibold hover:underline">{t('termsLink')}</span>
              </label>
            </div>
            {validationErrors.terms && (
              <p className="text-xs text-destructive -mt-2">{t(validationErrors.terms)}</p>
            )}

            {/* Submit */}
            <button type="submit" disabled={isLoading} className="med-btn-primary">
              {isLoading ? (
                <><Loader2 className="w-4 h-4 animate-spin" /><span>{t('loading')}</span></>
              ) : (
                <span>{t('signUpButton')}</span>
              )}
            </button>
          </form>

          {/* Footer */}
          <p className="mt-6 text-center text-sm text-muted-foreground">
            {t('haveAccount')}{' '}
            <button
              onClick={onLoginClick}
              className="font-semibold text-primary hover:text-primary/80 transition-colors"
            >
              {t('loginLink')}
            </button>
          </p>
        </div>
      </div>
    </div>
  );
}
