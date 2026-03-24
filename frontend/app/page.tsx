import { LandingHeader } from '@/components/landing-header';
import { LandingMain } from '@/components/landing-main';
import { LandingFooter } from '@/components/landing-footer';

export default function Home() {
  return (
    <div
      className="relative flex min-h-screen w-full flex-col overflow-x-hidden bg-background text-foreground selection:bg-primary/20"
    >
      <div className="layout-container flex h-full grow flex-col">
        <LandingHeader />
        <LandingMain />
        <LandingFooter />
      </div>
    </div>
  );
}
