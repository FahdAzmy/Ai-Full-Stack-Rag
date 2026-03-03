'use client';

import { getPasswordStrength } from '@/lib/validation';
import { useLanguage } from '@/lib/language-context';

interface PasswordStrengthIndicatorProps {
  password: string;
}

export function PasswordStrengthIndicator({ password }: PasswordStrengthIndicatorProps) {
  const strength = getPasswordStrength(password);
  const { t } = useLanguage();

  const strengthConfig = {
    weak: { color: 'bg-red-500 shadow-[0_0_10px_rgba(239,68,68,0.5)]', labelKey: 'strengthWeak', textColor: 'text-red-500 dark:text-red-400' },
    fair: { color: 'bg-yellow-500 shadow-[0_0_10px_rgba(234,179,8,0.5)]', labelKey: 'strengthFair', textColor: 'text-yellow-600 dark:text-yellow-400' },
    good: { color: 'bg-blue-500 shadow-[0_0_10px_rgba(59,130,246,0.5)]', labelKey: 'strengthGood', textColor: 'text-blue-600 dark:text-blue-400' },
    strong: { color: 'bg-green-500 shadow-[0_0_10px_rgba(34,197,94,0.5)]', labelKey: 'strengthStrong', textColor: 'text-green-600 dark:text-green-400' },
  };

  const config = strengthConfig[strength];
  const progress = {
    weak: 25,
    fair: 50,
    good: 75,
    strong: 100,
  }[strength];

  if (!password) return null;

  return (
    <div className="space-y-2 animate-fade-in-up">
      <div className="flex items-center justify-between px-1">
        <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">{t('passwordStrength')}</span>
        <span className={`text-xs font-bold ${config.textColor} transition-colors duration-300`}>{t(config.labelKey)}</span>
      </div>
      <div className="w-full bg-border/30 rounded-full h-2 overflow-hidden backdrop-blur-sm">
        <div
          className={`h-full ${config.color} transition-all duration-500 ease-out`}
          style={{ width: `${progress}%` }}
        />
      </div>
      <p className="text-[10px] text-muted-foreground font-medium px-1 leading-snug opacity-80">
        {t('passwordRequirements')}
      </p>
    </div>
  );
}
