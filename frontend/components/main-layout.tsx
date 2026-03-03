'use client';

import { useEffect } from 'react';
import { useLanguage } from '@/lib/language-context';

export function MainLayout({ children }: { children: React.ReactNode }) {
  const { isRTL, language } = useLanguage();

  useEffect(() => {
    document.documentElement.dir = isRTL ? 'rtl' : 'ltr';
    document.documentElement.lang = language;
  }, [isRTL, language]);

  return (
    <div className={`min-h-screen transition-colors duration-300 ${isRTL ? 'rtl' : 'ltr'}`}>
      {children}
    </div>
  );
}
