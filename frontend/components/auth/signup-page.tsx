'use client';

import React, { useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { AppDispatch, RootState } from '@/store/store';
import { signup } from '@/store/auth/auth-actions';
import { clearError, setPendingEmail } from '@/store/auth/auth-slice';
import { useLanguage } from '@/lib/language-context';
import { validateEmail, validatePassword, validateFullName, validatePasswordMatch, type ValidationErrors } from '@/lib/validation';
import { Checkbox } from '@/components/ui/checkbox';
import { User, Mail, Lock } from 'lucide-react';
import { PasswordStrengthIndicator } from '@/components/password-strength-indicator';
import { AuthLogo, AuthAlert, AuthInput, AuthCard, AuthSubmit } from './auth-form-components';

interface SignUpPageProps {
  onSuccess?: () => void;
  onLoginClick?: () => void;
}

export function SignUpPage({ onSuccess, onLoginClick }: SignUpPageProps) {
  const { t } = useLanguage();
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
      <AuthLogo variant="desktop" />

      <AuthCard>
        <div className="mb-8">
          <AuthLogo variant="mobile" />
          <h2 className="text-xl font-bold text-foreground mb-2">{t('createAccountTitle')}</h2>
          <p className="text-sm font-medium text-muted-foreground">{t('createAccountSub')}</p>
        </div>

        {error && <AuthAlert type="error" message={error} />}
        {successMessage && <AuthAlert type="success" message={successMessage} />}

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Full Name */}
          <div className="space-y-1.5">
            <label htmlFor="fullName" className="block text-sm font-medium text-foreground">{t('fullName')}</label>
            <AuthInput
              id="fullName"
              name="fullName"
              type="text"
              placeholder={t('fullNamePlaceholder')}
              value={formData.fullName}
              onChange={handleChange}
              disabled={isLoading}
              icon={<User className="w-4 h-4" />}
              error={validationErrors.fullName}
            />
          </div>

          {/* Email Address */}
          <div className="space-y-1.5">
            <label htmlFor="email" className="block text-sm font-medium text-foreground">{t('email')}</label>
            <AuthInput
              id="email"
              name="email"
              type="email"
              placeholder={t('emailPlaceholder')}
              value={formData.email}
              onChange={handleChange}
              disabled={isLoading}
              icon={<Mail className="w-4 h-4" />}
              error={validationErrors.email}
            />
          </div>

          {/* Password */}
          <div className="space-y-1.5">
            <label htmlFor="password" className="block text-sm font-medium text-foreground">{t('password')}</label>
            <AuthInput
              id="password"
              name="password"
              type="password"
              placeholder={t('passwordPlaceholder')}
              value={formData.password}
              onChange={handleChange}
              disabled={isLoading}
              icon={<Lock className="w-4 h-4" />}
              error={validationErrors.password}
            />
            {formData.password && !validationErrors.password && (
              <div className="mt-1">
                <PasswordStrengthIndicator password={formData.password} />
              </div>
            )}
          </div>

          {/* Confirm Password */}
          <div className="space-y-1.5">
            <label htmlFor="confirmPassword" className="block text-sm font-medium text-foreground">{t('confirmPassword')}</label>
            <AuthInput
              id="confirmPassword"
              name="confirmPassword"
              type="password"
              placeholder={t('confirmPasswordPlaceholder')}
              value={formData.confirmPassword}
              onChange={handleChange}
              disabled={isLoading}
              icon={<Lock className="w-4 h-4" />}
              error={validationErrors.confirmPassword}
            />
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
          <AuthSubmit loading={isLoading} className="mt-4">
            <span>{t('signUpButton')}</span>
          </AuthSubmit>
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
      </AuthCard>
    </>
  );
}
