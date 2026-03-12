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
        <div className="mb-8">
          {/* Mobile Logo Logo */}
          <div className="flex items-center gap-2 mb-6 md:hidden">
            <div className="size-8 bg-primary text-primary-foreground flex items-center justify-center rounded-lg shadow-sm">
              <span className="material-symbols-outlined !text-2xl">auto_stories</span>
            </div>
            <span className="font-bold text-lg text-foreground">{t('scholarGpt') || 'ScholarGPT'}</span>
          </div>
          
          <h2 className="text-xl font-bold text-foreground mb-2">{t('createAccountTitle')}</h2>
          <p className="text-sm font-medium text-muted-foreground">{t('createAccountSub')}</p>
        </div>

        {/* Error/Success Alert */}
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

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Full Name */}
          <div className="space-y-1.5">
            <label htmlFor="fullName" className="block text-sm font-medium text-foreground">{t('fullName')}</label>
            <div className="relative">
              <User className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <input
                id="fullName"
                name="fullName"
                type="text"
                placeholder={t('fullNamePlaceholder')}
                value={formData.fullName}
                onChange={handleChange}
                disabled={isLoading}
                className={`w-full pl-10 pr-4 py-2.5 bg-background border ${validationErrors.fullName ? 'border-destructive focus:ring-destructive/20 focus:border-destructive' : 'border-input focus:ring-primary/20 focus:border-primary'} text-foreground rounded-xl focus:ring-4 outline-none transition-all placeholder:text-muted-foreground font-medium`}
              />
            </div>
            {validationErrors.fullName && (
              <p className="text-xs font-medium text-destructive mt-1.5">{t(validationErrors.fullName)}</p>
            )}
          </div>

          {/* Email Address */}
          <div className="space-y-1.5">
            <label htmlFor="email" className="block text-sm font-medium text-foreground">{t('email')}</label>
            <div className="relative">
              <Mail className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <input
                id="email"
                name="email"
                type="email"
                placeholder={t('emailPlaceholder')}
                value={formData.email}
                onChange={handleChange}
                disabled={isLoading}
                className={`w-full pl-10 pr-4 py-2.5 bg-background border ${validationErrors.email ? 'border-destructive focus:ring-destructive/20 focus:border-destructive' : 'border-input focus:ring-primary/20 focus:border-primary'} text-foreground rounded-xl focus:ring-4 outline-none transition-all placeholder:text-muted-foreground font-medium`}
              />
            </div>
            {validationErrors.email && (
              <p className="text-xs font-medium text-destructive mt-1.5">{t(validationErrors.email)}</p>
            )}
          </div>

          {/* Password */}
          <div className="space-y-1.5">
            <label htmlFor="password" className="block text-sm font-medium text-foreground">{t('password')}</label>
            <div className="relative">
              <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <input
                id="password"
                name="password"
                type="password"
                placeholder={t('passwordPlaceholder')}
                value={formData.password}
                onChange={handleChange}
                disabled={isLoading}
                className={`w-full pl-10 pr-4 py-2.5 bg-background border ${validationErrors.password ? 'border-destructive focus:ring-destructive/20 focus:border-destructive' : 'border-input focus:ring-primary/20 focus:border-primary'} text-foreground rounded-xl focus:ring-4 outline-none transition-all placeholder:text-muted-foreground font-medium`}
              />
            </div>
            {formData.password && !validationErrors.password && (
              <div className="mt-1">
                <PasswordStrengthIndicator password={formData.password} />
              </div>
            )}
            {validationErrors.password && (
              <p className="text-xs font-medium text-destructive mt-1.5">{t(validationErrors.password)}</p>
            )}
          </div>

          {/* Confirm Password */}
          <div className="space-y-1.5">
            <label htmlFor="confirmPassword" className="block text-sm font-medium text-foreground">{t('confirmPassword')}</label>
            <div className="relative">
              <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <input
                id="confirmPassword"
                name="confirmPassword"
                type="password"
                placeholder={t('confirmPasswordPlaceholder')}
                value={formData.confirmPassword}
                onChange={handleChange}
                disabled={isLoading}
                className={`w-full pl-10 pr-4 py-2.5 bg-background border ${validationErrors.confirmPassword ? 'border-destructive focus:ring-destructive/20 focus:border-destructive' : 'border-input focus:ring-primary/20 focus:border-primary'} text-foreground rounded-xl focus:ring-4 outline-none transition-all placeholder:text-muted-foreground font-medium`}
              />
            </div>
            {validationErrors.confirmPassword && (
              <p className="text-xs font-medium text-destructive mt-1.5">{t(validationErrors.confirmPassword)}</p>
            )}
          </div>

          {/* Terms */}
          <div className={`flex items-start gap-3 mt-4 p-3 rounded-lg border ${validationErrors.terms ? 'border-destructive/30 bg-destructive/5' : 'border-transparent bg-muted/30'}`}>
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
            <p className="text-xs font-medium text-destructive mt-1">{t(validationErrors.terms)}</p>
          )}

          {/* Submit Button */}
          <button 
            type="submit" 
            disabled={isLoading} 
            className="w-full bg-primary hover:bg-primary-light text-primary-foreground font-bold py-3 mt-4 rounded-xl shadow-md hover:shadow-lg transition-all flex items-center justify-center gap-2 active:scale-[0.98]"
          >
            {isLoading ? (
              <><Loader2 className="w-5 h-5 animate-spin" /><span>{t('loading')}</span></>
            ) : (
              <span>{t('signUpButton')}</span>
            )}
          </button>
        </form>

        <div className="mt-8 pt-6 border-t border-border text-center">
          <p className="text-sm font-medium text-muted-foreground">
            {t('haveAccount')}{' '}
            <button
              onClick={onLoginClick}
              className="font-bold hover:underline text-primary hover:text-primary-light transition-colors"
            >
              {t('loginLink')}
            </button>
          </p>
        </div>
      </div>
    </>
  );
}
