'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useSelector } from 'react-redux';
import { ThemeSwitcher } from '@/components/theme-switcher';
import { LanguageSwitcher } from '@/components/language-switcher';
import { useLanguage } from '@/lib/language-context';
import { RootState } from '@/store/store';

export function LandingHeader() {
  const { t } = useLanguage();
  const router = useRouter();
  const { isAuthenticated } = useSelector((state: RootState) => state.auth);

  const handleCTAClick = () => {
    if (isAuthenticated) {
      router.push('/chat');
    } else {
      router.push('/auth');
    }
  };

  return (
    <header className="flex items-center justify-between whitespace-nowrap border-b border-primary/10 px-6 md:px-20 py-4 bg-background/80 backdrop-blur-md sticky top-0 z-50 transition-colors duration-300">
      
      {/* Brand & Logo */}
      <Link href="/" className="flex items-center gap-3 text-primary">
        <div className="size-8 flex items-center justify-center bg-primary text-primary-foreground rounded-lg shadow-sm">
          <span className="material-symbols-outlined text-xl">auto_stories</span>
        </div>
        <h2 className="text-primary text-xl font-bold tracking-tight">{t('scholarGpt')}</h2>
      </Link>

      {/* Navigation & Controls */}
      <div className="flex flex-1 justify-end gap-4 md:gap-8 items-center">

        {/* Global Controls & Auth */}
        <div className="flex items-center gap-3 md:gap-4 pl-0 md:pl-4 border-l border-border/50">
          
          {/* Custom Switchers */}
          <LanguageSwitcher />
          <ThemeSwitcher />
          
          {/* CTA Button — always says Get Started, routes based on auth */}
          <button
            onClick={handleCTAClick}
            className="hidden sm:flex min-w-[100px] cursor-pointer items-center justify-center rounded-xl h-10 px-5 bg-primary text-primary-foreground text-sm font-bold transition-all hover:bg-primary/90 hover:scale-[1.02] active:scale-95 shadow-md hover:shadow-primary/20"
          >
            <span>{t('getStarted')}</span>
          </button>
        </div>
      </div>
    </header>
  );
}
