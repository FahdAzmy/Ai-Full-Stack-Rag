'use client';

import React, { useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useRouter } from 'next/navigation';
import { AppDispatch, RootState } from '@/store/store';
import { login } from '@/store/auth/auth-actions';
import { clearError } from '@/store/auth/auth-slice';
import { useLanguage } from '@/lib/language-context';
import { validateEmail, validateLoginPassword, type ValidationErrors } from '@/lib/validation';
import { Input } from '@/components/ui/input';
import { Loader2, Mail, Lock, Stethoscope, ShieldCheck, Clock, Zap, AlertCircle } from 'lucide-react';

interface LoginPageProps {
  onSignUpClick?: () => void;
  onForgotPasswordClick?: () => void;
}

export function LoginPage({ onSignUpClick, onForgotPasswordClick }: LoginPageProps) {
  const { t, isRTL } = useLanguage();
  const dispatch = useDispatch<AppDispatch>();
  const router = useRouter();
  const { isLoading, error, isAuthenticated } = useSelector((state: RootState) => state.auth);

  const [formData, setFormData] = useState({ email: '', password: '' });
  const [validationErrors, setValidationErrors] = useState<ValidationErrors>({});

  // Redirect to chat when authenticated
  useEffect(() => {
    if (isAuthenticated) {
      router.push('/chat');
    }
  }, [isAuthenticated, router]);

  useEffect(() => {
    return () => { dispatch(clearError()); };
  }, [dispatch]);

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

  const validateForm = (): boolean => {
    const newErrors: ValidationErrors = {};
    const emailError = validateEmail(formData.email);
    if (emailError) newErrors.email = emailError;
    const passwordError = validateLoginPassword(formData.password);
    if (passwordError) newErrors.password = passwordError;
    setValidationErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!validateForm()) return;
    dispatch(login(formData));
  };

  return (
    <div className={`auth-layout ${isRTL ? 'rtl' : 'ltr'}`}>

      {/* ── Left Branding Panel ── */}
      <div className="auth-panel-left">
        {/* Logo */}
        <div className="relative z-10">
          <div className="flex items-center gap-3 mb-16">
            <div className="w-10 h-10 rounded-xl bg-white/20 flex items-center justify-center">
              <Stethoscope className="w-6 h-6 text-white" />
            </div>
            <span className="text-white font-bold text-xl tracking-tight">{t('brandName')}</span>
          </div>

          {/* Headline */}
          <h1 className="text-4xl font-bold text-white leading-tight mb-4">
            {t('loginHeadline')}
          </h1>
          <p className="text-teal-100 text-base leading-relaxed mb-12">
            {t('loginSubheadline')}
          </p>

          {/* Features */}
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

        {/* Bottom tagline */}
        <p className="relative z-10 text-teal-200 text-xs">
          {t('copyright')}
        </p>
      </div>

      {/* ── Right Form Panel ── */}
      <div className="auth-panel-right">
        <div className="auth-form-card">

          {/* Header */}
          <div className="mb-8">
            {/* Mobile logo */}
            <div className="flex items-center gap-2 mb-8 lg:hidden">
              <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: 'linear-gradient(135deg,#0d9488,#0f766e)' }}>
                <Stethoscope className="w-4 h-4 text-white" />
              </div>
              <span className="font-bold text-base text-foreground">{t('brandName')}</span>
            </div>

            <h2 className="text-2xl font-bold text-foreground mb-1">{t('welcomeBackTitle')}</h2>
            <p className="text-muted-foreground text-sm">{t('welcomeBackSub')}</p>
          </div>

          {/* Error */}
          {error && (
            <div className="med-alert-error">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              <span>{t(error)}</span>
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-4">

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
              <div className="flex justify-between items-center">
                <label className="text-sm font-medium text-foreground">{t('password')}</label>
                <button
                  type="button"
                  onClick={onForgotPasswordClick}
                  className="text-xs font-medium text-primary hover:text-primary/80 transition-colors"
                >
                  {t('forgotPassword')}
                </button>
              </div>
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
              {validationErrors.password && (
                <p className="text-xs text-destructive">{t(validationErrors.password)}</p>
              )}
            </div>

            {/* Submit */}
            <button type="submit" disabled={isLoading} className="med-btn-primary mt-2">
              {isLoading ? (
                <><Loader2 className="w-4 h-4 animate-spin" /><span>{t('loading')}</span></>
              ) : (
                <span>{t('loginButton')}</span>
              )}
            </button>
          </form>

          {/* Footer */}
          <p className="mt-6 text-center text-sm text-muted-foreground">
            {t('noAccount')}{' '}
            <button
              onClick={onSignUpClick}
              className="font-semibold text-primary hover:text-primary/80 transition-colors"
            >
              {t('signUpLink')}
            </button>
          </p>
        </div>
      </div>
    </div>
  );
}
