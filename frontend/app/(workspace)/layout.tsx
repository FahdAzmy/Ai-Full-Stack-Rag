'use client';

import { useState } from 'react';
import { usePathname } from 'next/navigation';
import { ChatSidebar } from '@/components/chat/chat-sidebar';

export default function WorkspaceLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const activeView = pathname?.includes('/documents') ? 'documents' : 'chat';
  const [sidebarOpen, setSidebarOpen] = useState(true);

  return (
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
  );
}
