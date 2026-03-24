'use client';

import { Suspense, useEffect } from 'react';
import { usePathname } from 'next/navigation';
import { useDispatch, useSelector } from 'react-redux';
import { RootState } from '@/store/store';
import { setSidebarOpen } from '@/store/chat/chat-slice';
import { ChatSidebar } from '@/components/chat/chat-sidebar';
import { AuthGuard } from '@/components/auth/auth-guard';
import { SectionErrorBoundary } from '@/components/error-boundary';

export default function WorkspaceLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const dispatch = useDispatch();
  const activeView = pathname?.includes('/documents') ? 'documents' : 'chat';
  const sidebarOpen = useSelector((state: RootState) => state.chat.sidebarOpen);

  // Use matchMedia instead of resize listener to avoid dispatching on every pixel
  useEffect(() => {
    const mql = window.matchMedia('(min-width: 1024px)');

    const onChange = (e: MediaQueryListEvent | MediaQueryList) => {
      dispatch(setSidebarOpen(e.matches));
    };

    // Initial check
    onChange(mql);

    mql.addEventListener('change', onChange as (e: MediaQueryListEvent) => void);
    return () => mql.removeEventListener('change', onChange as (e: MediaQueryListEvent) => void);
  }, [dispatch]);

  return (
    <AuthGuard>
      <div className="chat-page flex flex-col h-screen bg-white dark:bg-gray-950">
        <div className="flex flex-1 overflow-hidden">
          <SectionErrorBoundary section="Sidebar">
            <ChatSidebar
              isOpen={sidebarOpen}
              activeView={activeView}
            />
          </SectionErrorBoundary>
          <main
            id="workspace-main"
            className="flex-1 flex flex-col bg-white dark:bg-gray-950 overflow-hidden"
            role="main"
            aria-label="Main workspace content"
          >
            <Suspense
              fallback={
                <div className="flex-1 flex items-center justify-center">
                  <div className="flex flex-col items-center gap-3">
                    <span className="material-symbols-outlined text-3xl text-primary animate-spin" aria-hidden="true">
                      progress_activity
                    </span>
                    <p className="text-sm text-slate-500 font-medium">Loading...</p>
                  </div>
                </div>
              }
            >
              <SectionErrorBoundary section="Content">
                {children}
              </SectionErrorBoundary>
            </Suspense>
          </main>
        </div>
      </div>
    </AuthGuard>
  );
}
