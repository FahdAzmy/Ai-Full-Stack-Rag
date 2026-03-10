'use client';

import Link from 'next/link';
import { ThemeSwitcher } from '@/components/theme-switcher';
import { LanguageSwitcher } from '@/components/language-switcher';
import { useLanguage } from '@/lib/language-context';

export function LandingHeader() {
  const { t } = useLanguage();

  return (
    <header className="flex items-center justify-between whitespace-nowrap border-b border-primary/10 px-6 md:px-20 py-4 bg-background/80 backdrop-blur-md sticky top-0 z-50 transition-colors duration-300">
      
      {/* Brand & Logo */}
      <div className="flex items-center gap-3 text-primary">
        <div className="size-8 flex items-center justify-center bg-primary text-primary-foreground rounded-lg shadow-sm">
          {/* Using Google Material Symbols (needs to be loaded in layout.tsx) */}
          <span className="material-symbols-outlined text-xl">auto_stories</span>
        </div>
        <h2 className="text-primary text-xl font-bold tracking-tight">{t('scholarGpt')}</h2>
      </div>

      {/* Navigation & Controls */}
      <div className="flex flex-1 justify-end gap-4 md:gap-8 items-center">
     

        {/* Global Controls & Auth */}
        <div className="flex items-center gap-3 md:gap-4 pl-0 md:pl-4 border-l border-border/50">
          
          {/* Custom Switchers */}
          <LanguageSwitcher />
          <ThemeSwitcher />
          
          {/* CTA Button */}
          <button className="hidden sm:flex min-w-[100px] cursor-pointer items-center justify-center rounded-xl h-10 px-5 bg-primary text-primary-foreground text-sm font-bold transition-all hover:bg-primary/90 hover:scale-[1.02] active:scale-95 shadow-md hover:shadow-primary/20">
            <span>{t('getStarted')}</span>
          </button>

          {/* User Profile Thumbnail */}
          <div className="bg-primary/10 rounded-full p-0.5 border border-primary/20 hidden sm:flex items-center justify-center ml-2 transition-transform hover:scale-105 cursor-pointer">
            <div 
              className="bg-center bg-no-repeat aspect-square bg-cover rounded-full size-9" 
              aria-label="Professional profile photo of a researcher" 
              style={{ backgroundImage: 'url("https://lh3.googleusercontent.com/aida-public/AB6AXuDfPJgDznx7ln10FqS7V-OlFyRg1GKxwgxFvihUIPOpfBf6JpRfoEeePgimcZ1WHHZrlm6OTg_JCuMXrSnNmy44RyXaKlJOzfHInjXKUYw7X1_H_k73ng4I9hKY2FhfU3ADf4eAdOJ5nsmuf3CAHK9icxE8gzbsbVxoAz2ewniFBo6U5aLiUa1YEi3g4mt7lCL8v2d4feiAwwQmbN2IRccQRNqhmge9CZtqLDlPcE-jbNHRkBl8V8kmm69m6bZoTFGjsnKpgx0APJw")' }}
            />
          </div>
        </div>
      </div>
    </header>
  );
}
