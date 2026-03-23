'use client';

import { useEffect } from 'react';
import { usePathname } from 'next/navigation';
import { useDispatch, useSelector } from 'react-redux';
import { RootState } from '@/store/store';
import { setSidebarOpen } from '@/store/chat/chat-slice';
import { ChatSidebar } from '@/components/chat/chat-sidebar';
import { AuthGuard } from '@/components/auth/auth-guard';

export default function WorkspaceLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const dispatch = useDispatch();
  const activeView = pathname?.includes('/documents') ? 'documents' : 'chat';
  const sidebarOpen = useSelector((state: RootState) => state.chat.sidebarOpen);

  // Close sidebar by default on mobile, open on desktop
  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth < 1024) {
        dispatch(setSidebarOpen(false));
      } else {
        dispatch(setSidebarOpen(true));
      }
    };
    
    // Initial check
    handleResize();

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [dispatch]);

  return (
    <AuthGuard>
      <div className="chat-page flex flex-col h-screen bg-white dark:bg-gray-950">
        <div className="flex flex-1 overflow-hidden">
          <ChatSidebar
            isOpen={sidebarOpen}
            activeView={activeView}
          />
          <main className="flex-1 flex flex-col bg-white dark:bg-gray-950 overflow-hidden">
            {children}
          </main>
        </div>
      </div>
    </AuthGuard>
  );
}
