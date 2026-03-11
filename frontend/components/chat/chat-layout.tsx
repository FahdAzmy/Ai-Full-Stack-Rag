'use client';

import { useLanguage } from '@/lib/language-context';
import { useState, useRef, useEffect } from 'react';
import { ChatMessages } from './chat-messages';
import { ChatInput } from './chat-input';

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

export interface Conversation {
  id: string;
  title: string;
  active: boolean;
}

export function ChatLayout() {
  const { t, isRTL } = useLanguage();

  const getSampleConversations = (): Conversation[] => [
    { id: '1', title: t('chatConv1'), active: true },
    { id: '2', title: t('chatConv2'), active: false },
    { id: '3', title: t('chatConv3'), active: false },
    { id: '4', title: t('chatConv4'), active: false },
  ];

  const listDir = isRTL ? 'pr-5' : 'pl-5';

  const getSampleMessages = (): Message[] => [
    {
      id: '1',
      role: 'assistant',
      content: t('chatGreeting'),
      timestamp: 'Just now',
    },
    {
      id: '2',
      role: 'user',
      content: t('chatMsg1'),
      timestamp: '10:45 AM',
    },
    {
      id: '3',
      role: 'assistant',
      content: `<p class="mb-3">${t('chatReply1Intro')}</p>
<ul class="list-disc ${listDir} space-y-1.5">
  <li>${t('chatReply1Item1')}</li>
  <li>${t('chatReply1Item2')}</li>
  <li>${t('chatReply1Item3')}</li>
</ul>`,
      timestamp: '10:46 AM',
    },
    {
      id: '4',
      role: 'user',
      content: t('chatMsg2'),
      timestamp: '10:48 AM',
    },
    {
      id: '5',
      role: 'assistant',
      content: `<p class="mb-2">${t('chatReply2Intro')}</p>
<p class="mb-2">${t('chatReply2Cipro')}</p>
<p>${t('chatReply2Amox')}</p>`,
      timestamp: '10:49 AM',
    },
  ];

  const [messages, setMessages] = useState<Message[]>(getSampleMessages());
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Re-generate sample data when language changes
  useEffect(() => {
    setMessages(getSampleMessages());
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isRTL]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = (content: string) => {
    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };
    setMessages((prev) => [...prev, userMessage]);
    setIsTyping(true);

    // Simulate AI response
    setTimeout(() => {
      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: t('chatAiResponse'),
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, aiMessage]);
      setIsTyping(false);
    }, 1500);
  };



  return (
    <div className="flex h-full w-full bg-white dark:bg-background-dark overflow-hidden font-display relative">
      {/* Main Content Area */}
      <div className="flex-1 flex flex-col relative bg-white dark:bg-background-dark">
        {/* Header */}
        <header className="h-16 border-b border-border-cream dark:border-gray-800 flex items-center justify-between px-8 bg-white/80 dark:bg-background-dark/80 backdrop-blur-md sticky top-0 z-10 transition-colors">
          <div className="flex items-center gap-4">
            <span className="material-symbols-outlined text-primary/40 dark:text-emerald-500/40">menu_open</span>
            <h2 className="text-sm font-semibold text-primary dark:text-emerald-400">Quantum Computing Paradigms Analysis</h2>
          </div>
       
        </header>

        {/* Chat Area */}
        <ChatMessages
          messages={messages}
          isTyping={isTyping}
          messagesEndRef={messagesEndRef}
        />

        {/* Input Area */}
        <ChatInput onSend={handleSendMessage} />
      </div>

     
    </div>
  );
}
