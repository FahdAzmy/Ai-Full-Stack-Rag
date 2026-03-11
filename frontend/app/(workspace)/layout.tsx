'use client';

import { useLanguage } from '@/lib/language-context';
import { useState, useRef, useEffect } from 'react';
import { usePathname } from 'next/navigation';
import { ChatSidebar } from '@/components/chat/chat-sidebar';
import { Conversation } from '@/components/chat/chat-layout';

export default function WorkspaceLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { t, isRTL } = useLanguage();
  const pathname = usePathname();
  const activeView = pathname?.includes('/documents') ? 'documents' : 'chat';

  const getSampleConversations = (): Conversation[] => [
    { id: '1', title: t('chatConv1'), active: true },
    { id: '2', title: t('chatConv2'), active: false },
    { id: '3', title: t('chatConv3'), active: false },
    { id: '4', title: t('chatConv4'), active: false },
  ];

  const [conversations, setConversations] = useState<Conversation[]>(getSampleConversations());
  const [sidebarOpen, setSidebarOpen] = useState(true);

  useEffect(() => {
    setConversations(getSampleConversations());
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isRTL]);

  const handleNewConversation = () => {
    const newConv: Conversation = {
      id: Date.now().toString(),
      title: t('chatNewConversation'),
      active: true,
    };
    setConversations((prev) => prev.map((c) => ({ ...c, active: false })).concat(newConv));
  };

  const handleSelectConversation = (id: string) => {
    setConversations((prev) => prev.map((c) => ({ ...c, active: c.id === id })));
  };

  return (
    <div className="chat-page flex flex-col h-screen bg-white dark:bg-gray-950">
      <div className="flex flex-1 overflow-hidden">
        <ChatSidebar
          conversations={conversations}
          isOpen={sidebarOpen}
          activeView={activeView}
          onViewChange={() => {}}
          onNewConversation={handleNewConversation}
          onSelectConversation={handleSelectConversation}
        />
        <main className="flex-1 flex flex-col bg-white dark:bg-gray-950 overflow-hidden">
          {children}
        </main>
      </div>
    </div>
  );
}
