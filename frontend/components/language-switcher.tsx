'use client';

import { useLanguage } from '@/lib/language-context';
import { Button } from '@/components/ui/button';
import { Globe } from 'lucide-react';

export function LanguageSwitcher() {
  const { language, setLanguage, t } = useLanguage();

  return (
    <div className="flex gap-1 bg-card/80 backdrop-blur-sm p-1 rounded-lg border border-border shadow-lg">
      <Button
        variant={language === 'en' ? 'default' : 'ghost'}
        size="sm"
        onClick={() => setLanguage('en')}
        className="min-w-max transition-all duration-200"
      >
        <Globe className="w-4 h-4 mr-1.5" />
        {t('english')}
      </Button>
      <Button
        variant={language === 'ar' ? 'default' : 'ghost'}
        size="sm"
        onClick={() => setLanguage('ar')}
        className="min-w-max transition-all duration-200"
      >
        {t('arabic')}
        <Globe className="w-4 h-4 ml-1.5" />
      </Button>
    </div>
  );
}
