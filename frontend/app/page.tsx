'use client';

import { LandingHeader } from '@/components/landing-header';
import { LandingMain } from '@/components/landing-main';
import { LandingFooter } from '@/components/landing-footer';
import { useLanguage } from '@/lib/language-context';

export default function Home() {
  const { isRTL } = useLanguage();

  return (
    <div 
      className="relative flex min-h-screen w-full flex-col overflow-x-hidden bg-background text-foreground selection:bg-primary/20"
      dir={isRTL ? 'rtl' : 'ltr'}
    >
      <div className="layout-container flex h-full grow flex-col">
          <LandingHeader />
          <LandingMain />
          <LandingFooter />
      </div>
    </div>
  );
}
