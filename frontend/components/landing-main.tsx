'use client';

import React from 'react';
import { useLanguage } from '@/lib/language-context';

export function LandingMain() {
  const { t } = useLanguage();

  return (
    <main className="flex-1 flex flex-col">
      {/* Hero Section */}
      <section className="relative w-full max-w-[1200px] mx-auto px-6 py-16 md:py-24 lg:py-32 overflow-hidden">
        {/* Subtle mesh background effect (from frontend-design philosophy) */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] md:w-[800px] h-[600px] md:h-[800px] bg-primary/5 dark:bg-primary/10 rounded-full blur-[100px] -z-20 pointer-events-none" />
        
        <div className="flex flex-col gap-12 lg:flex-row items-center relative z-10">
          
          {/* Left Text Column */}
          <div className="flex flex-col gap-8 flex-1">
            <div className="flex flex-col gap-5">
              <span className="text-primary dark:text-primary-light font-bold tracking-widest text-xs uppercase bg-primary/10 w-fit px-3 py-1 rounded-full border border-primary/20 shadow-sm">
                {t('heroBadge')}
              </span>
              <h1 className="text-foreground text-5xl md:text-6xl lg:text-7xl font-black leading-[1.1] tracking-tight">
                {t('heroTitle')} <span className="text-primary bg-clip-text">{t('heroTitleHighlight')}</span>
              </h1>
              <p className="text-muted-foreground text-lg md:text-xl font-normal leading-relaxed max-w-[540px]">
                {t('heroSubtitle')}
              </p>
            </div>
            
            <div className="flex flex-wrap gap-4">
              <button className="flex min-w-[180px] cursor-pointer items-center justify-center rounded-xl h-14 px-8 bg-primary text-primary-foreground text-lg font-bold shadow-[0_8px_30px_rgb(6,78,59,0.2)] hover:bg-primary-light hover:shadow-[0_8px_30px_rgb(6,78,59,0.3)] hover:-translate-y-0.5 transition-all active:scale-95 duration-300">
                {t('heroPrimaryBtn')}
              </button>
              <button className="flex min-w-[180px] cursor-pointer items-center justify-center rounded-xl h-14 px-8 bg-transparent backdrop-blur-sm border-2 border-primary/20 text-foreground text-lg font-bold hover:bg-primary/5 hover:border-primary/40 transition-all hover:-translate-y-0.5 active:scale-95 duration-300">
                {t('heroSecondaryBtn')}
              </button>
            </div>

            <div className="flex items-center gap-3 text-muted-foreground pt-2">
              <span className="material-symbols-outlined text-primary text-xl">verified_user</span>
              <span className="text-sm font-medium">{t('heroTrust')}</span>
            </div>
          </div>

          {/* Right Image Column */}
          <div className="flex-1 w-full relative group">
            <div className="absolute -inset-4 bg-gradient-to-tr from-primary/15 to-primary/5 rounded-[2.5rem] rotate-3 -z-10 transition-transform duration-700 group-hover:rotate-6 blur-sm" />
            <div className="absolute -inset-4 bg-primary/10 rounded-[2.5rem] -rotate-2 -z-10 transition-transform duration-700 group-hover:-rotate-3" />
            
            <div className="w-full aspect-[4/3] bg-card rounded-2xl overflow-hidden shadow-2xl border border-border relative">
              <div 
                className="w-full h-full bg-cover bg-center transition-transform duration-700 group-hover:scale-105" 
                aria-label="Quiet library setting with open books and a laptop" 
                style={{ backgroundImage: 'url("https://lh3.googleusercontent.com/aida-public/AB6AXuAT8cx8m50TgnpbYzFz2cMRLvVyGvwqNWRUHnfk2maovsxgujmk5ckgP5kyYCQkOfdI_XXoliKYZJL9l2pB_K-hOJYKPURP-2soNYPYVqUH9f7iitjc_6tjYRFOfpiXEmfJVl61WyIKEjev8nZgqhC4jJsljzwrSPPYdmeIMhmFmGWAJUYSsbhak6fxsluGgiAYRWP_V3M4qJmRPZMoAn6l95skPPUSWryd1QxGREuYU_-96Sg_VR1wHPKuq0fkqkqHCKPZlkUBqqc")' }} 
              />
              <div className="absolute inset-0 ring-1 ring-inset ring-black/10 dark:ring-white/10 rounded-2xl pointer-events-none" />
            </div>
          </div>
        </div>
      </section>

      {/* Features Grid */}
      <section id="features" className="bg-primary/5 dark:bg-primary/5 border-y border-primary/10 py-24 relative overflow-hidden">
        {/* Subtle decorative mesh */}
        <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-primary/5 rounded-full blur-[80px] -z-10 translate-x-1/2 -translate-y-1/2" />
        
        <div className="max-w-[1200px] mx-auto px-6 relative z-10">
          <div className="flex flex-col gap-4 mb-16 text-center md:text-left">
            <h2 className="text-primary dark:text-primary-light text-sm font-bold uppercase tracking-widest">{t('featuresBadge')}</h2>
            <h3 className="text-foreground text-4xl md:text-5xl font-black leading-tight max-w-[700px]">
              {t('featuresTitle')}
            </h3>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 lg:gap-8">
            
            {/* Feature 1 */}
            <div className="flex flex-col gap-6 rounded-3xl border border-border bg-card p-8 shadow-sm hover:shadow-2xl hover:shadow-primary/10 hover:-translate-y-2 transition-all duration-500 group relative overflow-hidden">
              <div className="absolute top-0 right-0 p-3 opacity-0 group-hover:opacity-100 transition-opacity duration-500 text-primary/10 pointer-events-none">
                <span className="material-symbols-outlined text-[100px] leading-none">psychology</span>
              </div>
              <div className="w-14 h-14 rounded-2xl bg-primary/10 border border-primary/20 flex items-center justify-center text-primary group-hover:bg-primary group-hover:text-primary-foreground transition-colors duration-500 shadow-inner relative z-10">
                <span className="material-symbols-outlined text-3xl">psychology</span>
              </div>
              <div className="flex flex-col gap-3 relative z-10">
                <h4 className="text-foreground text-xl font-bold">{t('featureAiTitle')}</h4>
                <p className="text-muted-foreground leading-relaxed">{t('featureAiDesc')}</p>
              </div>
            </div>

            {/* Feature 2 */}
            <div className="flex flex-col gap-6 rounded-3xl border border-border bg-card p-8 shadow-sm hover:shadow-2xl hover:shadow-primary/10 hover:-translate-y-2 transition-all duration-500 group relative overflow-hidden">
              <div className="absolute top-0 right-0 p-3 opacity-0 group-hover:opacity-100 transition-opacity duration-500 text-primary/10 pointer-events-none">
                <span className="material-symbols-outlined text-[100px] leading-none">history_edu</span>
              </div>
              <div className="w-14 h-14 rounded-2xl bg-primary/10 border border-primary/20 flex items-center justify-center text-primary group-hover:bg-primary group-hover:text-primary-foreground transition-colors duration-500 shadow-inner relative z-10">
                <span className="material-symbols-outlined text-3xl">history_edu</span>
              </div>
              <div className="flex flex-col gap-3 relative z-10">
                <h4 className="text-foreground text-xl font-bold">{t('featureCitationTitle')}</h4>
                <p className="text-muted-foreground leading-relaxed">{t('featureCitationDesc')}</p>
              </div>
            </div>

            {/* Feature 3 */}
            <div className="flex flex-col gap-6 rounded-3xl border border-border bg-card p-8 shadow-sm hover:shadow-2xl hover:shadow-primary/10 hover:-translate-y-2 transition-all duration-500 group relative overflow-hidden">
              <div className="absolute top-0 right-0 p-3 opacity-0 group-hover:opacity-100 transition-opacity duration-500 text-primary/10 pointer-events-none">
                <span className="material-symbols-outlined text-[100px] leading-none">terminal</span>
              </div>
              <div className="w-14 h-14 rounded-2xl bg-primary/10 border border-primary/20 flex items-center justify-center text-primary group-hover:bg-primary group-hover:text-primary-foreground transition-colors duration-500 shadow-inner relative z-10">
                <span className="material-symbols-outlined text-3xl">terminal</span>
              </div>
              <div className="flex flex-col gap-3 relative z-10">
                <h4 className="text-foreground text-xl font-bold">{t('featureBibtexTitle')}</h4>
                <p className="text-muted-foreground leading-relaxed">{t('featureBibtexDesc')}</p>
              </div>
            </div>

          </div>
        </div>
      </section>

      {/* Interface Showcase */}
      <section className="py-24 max-w-[1200px] mx-auto px-6 w-full">
        <div className="flex flex-col md:flex-row items-center gap-12 rounded-[2.5rem] bg-primary p-6 md:p-12 text-primary-foreground overflow-hidden relative shadow-2xl shadow-primary/30">
          
          <div className="absolute top-0 right-0 w-64 h-64 bg-white/10 rounded-full -translate-y-1/2 translate-x-1/2 blur-3xl" />
          <div className="absolute bottom-0 left-0 w-64 h-64 bg-black/10 rounded-full translate-y-1/2 -translate-x-1/2 blur-3xl pointer-events-none" />

          {/* Left: Image Box */}
          <div className="w-full md:w-1/2 rounded-2xl overflow-hidden shadow-2xl ring-1 ring-white/10 relative group">
            <div className="w-full aspect-video bg-cover bg-center transition-transform duration-700 group-hover:scale-105" 
                 aria-label="Modern dark-themed research dashboard interface" 
                 style={{ backgroundImage: 'url("https://lh3.googleusercontent.com/aida-public/AB6AXuAhKiJfVzhaTbtBjjvaZdPvTJbByWm-2ZD3OlpP_332Yspj2hJSUhvuy1OkUH6nokQcInJbBDX3MOc_LWsopW13Infd1XKMGTpM1Y4cVlpRW5P0gAclhogmoB6D5_iUNRxMBioX4FrulglHZpzm9VV2-ilgiIbJO7dVs36moO-A6bJcU091auHGrqH5CAE6li9wJEdd3r1qLlkkIImuayg9tc9lArB2VzI-S4yWHxVX0LLbsbJKyou7MT6k-IIYlhpatt_fTwfUiTY")' }} 
            />
          </div>

          {/* Right: Text Box */}
          <div className="w-full md:w-1/2 flex flex-col gap-6 relative z-10 p-2">
            <h3 className="text-3xl md:text-4xl lg:text-5xl font-black text-primary-foreground tracking-tight">{t('interfaceShowcaseTitle')}</h3>
            <p className="text-primary-foreground/80 text-lg font-normal leading-relaxed">
              {t('interfaceShowcaseDesc')}
            </p>
            <div className="flex flex-col gap-4 mt-2">
              <div className="flex items-center gap-3">
                <span className="material-symbols-outlined text-green-300">check_circle</span>
                <span className="font-medium text-primary-foreground/90">{t('interfaceFeature1')}</span>
              </div>
              <div className="flex items-center gap-3">
                <span className="material-symbols-outlined text-green-300">check_circle</span>
                <span className="font-medium text-primary-foreground/90">{t('interfaceFeature2')}</span>
              </div>
            </div>
            <button className="flex w-fit cursor-pointer items-center justify-center rounded-xl h-12 px-8 bg-background text-primary text-sm font-bold mt-6 hover:bg-white hover:-translate-y-1 transition-all active:scale-95 shadow-lg">
              {t('interfaceBtn')}
            </button>
          </div>

        </div>
      </section>

      {/* Call to Action */}
      <section className="py-24 bg-background border-t border-border mt-auto">
        <div className="max-w-[800px] mx-auto px-6 flex flex-col items-center text-center gap-10">
          <div className="flex flex-col gap-5">
            <h2 className="text-foreground text-4xl md:text-5xl lg:text-6xl font-black tracking-tight leading-tight">
              {t('ctaTitle1')}<br className="hidden sm:block"/> {t('ctaTitle2')}
            </h2>
            <p className="text-muted-foreground text-lg md:text-xl">
              {t('ctaSubtitle')}
            </p>
          </div>
          <div className="w-full max-w-md">
            <div className="flex flex-col sm:flex-row gap-3 p-2 bg-muted/30 rounded-2xl border border-border shadow-sm focus-within:border-primary/50 focus-within:ring-4 focus-within:ring-primary/10 transition-all">
              <input 
                className="flex-1 bg-transparent border-none outline-none focus:ring-0 px-4 py-3 text-foreground placeholder-shown:text-muted-foreground font-medium" 
                placeholder={t('ctaInputPlaceholder')}
                type="email"
              />
              <button className="bg-primary text-primary-foreground px-8 py-3 rounded-xl font-bold hover:bg-primary-light transition-all shadow-md active:scale-95 whitespace-nowrap">
                {t('ctaWaitlist')}
              </button>
            </div>
            <p className="text-sm font-medium text-muted-foreground mt-4">{t('ctaNote')}</p>
          </div>
        </div>
      </section>

    </main>
  );
}
