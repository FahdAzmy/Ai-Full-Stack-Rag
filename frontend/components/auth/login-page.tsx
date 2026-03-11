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
    <>
      <div className="w-full max-w-[420px] mb-8 text-center animate-in fade-in slide-in-from-bottom-4 duration-500 hidden md:block">
        <div className="flex items-center justify-center gap-2 mb-4">
          <div className="size-10 bg-primary text-primary-foreground flex items-center justify-center rounded-lg shadow-sm">
            <span className="material-symbols-outlined !text-3xl">auto_stories</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground">{t('scholarGpt') || 'ScholarGPT'}</h1>
        </div>
      </div>

      <div className="w-full max-w-[420px] bg-card border border-border rounded-xl shadow-[0_10px_25px_-5px_rgba(6,76,57,0.05),0_8px_10px_-6px_rgba(6,76,57,0.05)] p-8 relative z-10 animate-in fade-in slide-in-from-bottom-8 duration-700">
        <div className="mb-8">
          {/* Mobile Logo Logo */}
          <div className="flex items-center gap-2 mb-6 md:hidden">
            <div className="size-8 bg-primary text-primary-foreground flex items-center justify-center rounded-lg shadow-sm">
              <span className="material-symbols-outlined !text-2xl">auto_stories</span>
            </div>
            <span className="font-bold text-lg text-foreground">{t('scholarGpt') || 'ScholarGPT'}</span>
          </div>
          
          <h2 className="text-xl font-bold text-foreground mb-2">{t('welcomeBackTitle')}</h2>
          <p className="text-sm font-medium text-muted-foreground">{t('welcomeBackSub')}</p>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="mb-6 p-4 rounded-xl bg-destructive/10 border border-destructive/20 flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-destructive flex-shrink-0 mt-0.5" />
            <p className="text-sm font-medium text-destructive">{t(error)}</p>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-5">
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
            <div className="flex justify-between items-center">
              <label htmlFor="password" className="block text-sm font-medium text-foreground">{t('password')}</label>
              <button
                type="button"
                onClick={onForgotPasswordClick}
                className="text-xs font-bold hover:underline py-1 px-1 rounded text-primary hover:text-primary-light transition-colors focus:outline-none"
              >
                {t('forgotPassword')}
              </button>
            </div>
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
                className={`w-full pl-10 pr-10 py-2.5 bg-background border ${validationErrors.password ? 'border-destructive focus:ring-destructive/20 focus:border-destructive' : 'border-input focus:ring-primary/20 focus:border-primary'} text-foreground rounded-xl focus:ring-4 outline-none transition-all placeholder:text-muted-foreground font-medium`}
              />
            </div>
            {validationErrors.password && (
              <p className="text-xs font-medium text-destructive mt-1.5">{t(validationErrors.password)}</p>
            )}
          </div>

          {/* Submit Button */}
          <button 
            type="submit" 
            disabled={isLoading} 
            className="w-full bg-primary hover:bg-primary-light text-primary-foreground font-bold py-3 mt-2 rounded-xl shadow-md hover:shadow-lg transition-all flex items-center justify-center gap-2 active:scale-[0.98]"
          >
            {isLoading ? (
              <><Loader2 className="w-5 h-5 animate-spin" /><span>{t('loading')}</span></>
            ) : (
              <span>{t('loginButton')}</span>
            )}
          </button>
        </form>

        <div className="mt-8 pt-6 border-t border-border text-center">
          <p className="text-sm font-medium text-muted-foreground">
            {t('noAccount')}{' '}
            <button
              onClick={onSignUpClick}
              className="font-bold hover:underline text-primary hover:text-primary-light transition-colors"
            >
              {t('signUpLink')}
            </button>
          </p>
        </div>
      </div>

      <div className="mt-8 flex flex-col items-center gap-4 text-center animate-in fade-in slide-in-from-bottom-8 duration-700 delay-150">
        <div className="flex -space-x-2">
          <div className="w-9 h-9 rounded-full border-2 border-background bg-slate-200 overflow-hidden shadow-sm">
            <img className="w-full h-full object-cover" alt="Researcher profile portrait" src="https://lh3.googleusercontent.com/aida-public/AB6AXuDX5NvuEGwxjSttGE_gb2OfqBVZ1DQy2G60MAUYPGPTLxflmm6YO-Fr2LDRYB6NbK2HEVUVLXrP5vJgvpyEbr1nMsaxgQWWkvb3rBuXBNyML672--goDcRbW0a-gcc4Lb_UciJPInK-YuEV0UJzdknlseEbElvhdB6gbMDG50j6DjxGNEPMYXLF1UMI4GAM9509NRCwvcpLPmOhoRZ8Y1uXfqEmzCkTAy9KwZAuJey2W6tHWcXrAw99G-s3_6BbYWqsjNQf5k1vmOA"/>
          </div>
          <div className="w-9 h-9 rounded-full border-2 border-background bg-slate-300 overflow-hidden shadow-sm">
            <img className="w-full h-full object-cover" alt="Student profile portrait" src="https://lh3.googleusercontent.com/aida-public/AB6AXuA7EiSMgwZHu3FWw3lixb4Kf1Ad32XaxlXWO2BP9qKUIrB8adyBtHdMLbY5SwheateEPkXNWQUr4mkW06fOkBcPXtxGSVxzGA-_7bsJUcbo93fj43wqkGiO0tSgcEUuN42-QmHuaTCkXOgE7FhGtl5ileBQiGJWv9BmzTgG-mvAyV2yhsVEevZzDXTmaigJ5QM-eTOomdUhPiM22qkgQJK9aiK6ucS1h97qatc50SgE2T9iuvYL1f6wb7BNkBCMtnlrbeS-45PWYGM"/>
          </div>
          <div className="w-9 h-9 rounded-full border-2 border-background bg-slate-400 overflow-hidden shadow-sm">
            <img className="w-full h-full object-cover" alt="Academic professional portrait" src="https://lh3.googleusercontent.com/aida-public/AB6AXuAfgicpnsxfRD2Gatup9QSu597elsC5QbM5-zrUczJrHsQUwSOKRg0fluBnKJuTu_bt8kWqnda4eN8QZWygJpjWKi4KDzZrW9wBdxQuZmk7LbAe3RGpiwSUvhdCcbPkoGs39xdBipBpYAXOCrOe5geLCEpTTC1UxklHPY0QGiJKO2w8OHv__tNt_kBYALdiFhV4ecaJ9OvGFEfEj5mQZZWxtvD1-Bq8kgnb_ZOXSe-BoeeBtioCvutyYwFYi-gprn-6dhre9V5T0PE"/>
          </div>
          <div className="w-9 h-9 rounded-full border-2 border-background bg-primary flex items-center justify-center text-[10px] font-bold text-primary-foreground shadow-sm">
            1M+
          </div>
        </div>
        <p className="text-xs text-muted-foreground uppercase tracking-widest font-bold">
          Securely processing over 1M+ research papers
        </p>
      </div>
    </>
  );
}
