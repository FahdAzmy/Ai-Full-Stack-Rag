import { LandingHeader } from '@/components/landing-header';
import { AuthManager } from '@/components/auth/auth-manager';

export default function AuthPage() {
  return (
    <div className="relative flex min-h-screen w-full flex-col overflow-x-hidden bg-[#fdfbf7] dark:bg-[#0a1410] text-slate-900 dark:text-slate-100 font-display">
      <div className="layout-container flex h-full grow flex-col">
        <LandingHeader />
        <main className="flex-1 flex flex-col">
          <AuthManager />
        </main>
      </div>
    </div>
  );
}
