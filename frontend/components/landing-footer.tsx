'use client';

import React from 'react';
import Link from 'next/link';
import { useLanguage } from '@/lib/language-context';

export function LandingFooter() {
  const { t } = useLanguage();

  return (
    <footer className="bg-background border-t border-border py-12 px-6 md:px-20 mt-auto">
      <div className="max-w-[1200px] mx-auto flex flex-col md:flex-row justify-between items-start md:items-center gap-10 md:gap-8">
        
        {/* Brand details */}
        <div className="flex flex-col gap-4">
          <div className="flex items-center gap-2 text-primary dark:text-primary-light font-bold">
            <span className="material-symbols-outlined text-2xl">auto_stories</span>
            <span className="text-xl tracking-tight">{t('scholarGpt')}</span>
          </div>
          <p className="text-sm font-medium text-muted-foreground max-w-xs leading-relaxed">
            {t('footerDesc')}
          </p>
        </div>

        {/* Navigation Links */}
        <div className="flex gap-16 md:gap-24">
          <div className="flex flex-col gap-4">
            <span className="text-foreground font-bold tracking-wide uppercase text-xs">{t('footerProduct')}</span>
            <Link className="text-sm font-medium text-muted-foreground hover:text-primary transition-colors" href="#features">{t('features')}</Link>
            <Link className="text-sm font-medium text-muted-foreground hover:text-primary transition-colors" href="#">{t('footerIntegrations')}</Link>
            <Link className="text-sm font-medium text-muted-foreground hover:text-primary transition-colors" href="#pricing">{t('pricing')}</Link>
          </div>
          <div className="flex flex-col gap-4">
            <span className="text-foreground font-bold tracking-wide uppercase text-xs">{t('footerLegal')}</span>
            <Link className="text-sm font-medium text-muted-foreground hover:text-primary transition-colors" href="#">{t('footerPrivacy')}</Link>
            <Link className="text-sm font-medium text-muted-foreground hover:text-primary transition-colors" href="#">{t('footerTerms')}</Link>
            <Link className="text-sm font-medium text-muted-foreground hover:text-primary transition-colors" href="#">{t('footerEthics')}</Link>
          </div>
        </div>
      </div>

      {/* Copyright & Bottom Bar */}
      <div className="max-w-[1200px] mx-auto border-t border-border mt-12 pt-8 flex flex-col md:flex-row justify-between items-center gap-4 text-xs font-medium text-muted-foreground">
        <p>{t('footerCopyright')}</p>
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full hover:bg-muted transition-colors cursor-pointer">
          <span className="material-symbols-outlined text-base">language</span>
          <span>{t('englishLabel')}</span>
        </div>
      </div>
    </footer>
  );
}
