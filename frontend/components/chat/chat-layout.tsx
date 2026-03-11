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
          <div className="flex items-center gap-3">
            <button className="p-2 hover:bg-background-light dark:hover:bg-gray-800 rounded-lg text-primary/60 dark:text-emerald-500/60 transition-colors">
              <span className="material-symbols-outlined">share</span>
            </button>
            <button className="p-2 hover:bg-background-light dark:hover:bg-gray-800 rounded-lg text-primary/60 dark:text-emerald-500/60 transition-colors">
              <span className="material-symbols-outlined">more_horiz</span>
            </button>
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

      {/* Right Citations Panel (Expandable) */}
      <aside className="w-80 flex-shrink-0 border-l border-border-cream dark:border-gray-800 bg-white dark:bg-background-dark overflow-y-auto hidden lg:flex flex-col transition-colors">
        <div className="p-6 border-b border-border-cream dark:border-gray-800 bg-background-light/50 dark:bg-gray-900 flex items-center justify-between transition-colors">
          <h3 className="text-sm font-bold text-primary dark:text-emerald-400 flex items-center gap-2">
            <span className="material-symbols-outlined text-lg">list_alt</span>
            Citations & Sources
          </h3>
          <span className="text-[10px] font-bold text-primary/40 dark:text-emerald-500/40 bg-primary/5 dark:bg-emerald-500/10 px-2 py-0.5 rounded-full">3 SOURCES</span>
        </div>
        <div className="p-4 space-y-4 flex-1 overflow-y-auto chat-scrollbar">
          {/* Citation Item 1 */}
          <div className="p-4 rounded-xl border border-border-cream dark:border-gray-800 bg-background-light/30 dark:bg-gray-900/50 hover:border-primary/30 dark:hover:border-emerald-500/30 transition-colors cursor-pointer group">
            <div className="flex items-start gap-3">
              <div className="size-6 rounded bg-primary dark:bg-emerald-600 text-white flex items-center justify-center text-[10px] font-bold shrink-0 shadow-sm">1</div>
              <div className="space-y-1">
                <p className="text-xs font-bold text-primary dark:text-emerald-300 leading-tight group-hover:text-accent dark:group-hover:text-emerald-400 transition-colors">Quantum Circuits and Universal Gate Sets</p>
                <p className="text-[10px] text-primary/60 dark:text-emerald-500/60 transition-colors">Preskill, J. (2023). Journal of Quantum Physics, 14(2), 112-145.</p>
                <div className="pt-2 flex gap-2">
                  <span className="text-[9px] px-2 py-0.5 bg-white dark:bg-gray-800 border border-border-cream dark:border-gray-700 rounded text-primary/50 dark:text-emerald-500/50 transition-colors shadow-sm">Core Theory</span>
                </div>
              </div>
            </div>
          </div>
          {/* Citation Item 2 */}
          <div className="p-4 rounded-xl border border-border-cream dark:border-gray-800 bg-white dark:bg-background-dark hover:border-primary/30 dark:hover:border-emerald-500/30 transition-colors cursor-pointer group shadow-sm">
            <div className="flex items-start gap-3">
              <div className="size-6 rounded bg-primary dark:bg-emerald-600 text-white flex items-center justify-center text-[10px] font-bold shrink-0 shadow-sm">2</div>
              <div className="space-y-1">
                <p className="text-xs font-bold text-primary dark:text-emerald-300 leading-tight group-hover:text-accent dark:group-hover:text-emerald-400 transition-colors">Evolutionary Dynamics in Adiabatic Systems</p>
                <p className="text-[10px] text-primary/60 dark:text-emerald-500/60 transition-colors">Farhi, E., et al. (2022). Science Advances.</p>
                <div className="pt-2 flex gap-2">
                  <span className="text-[9px] px-2 py-0.5 bg-white dark:bg-gray-800 border border-border-cream dark:border-gray-700 rounded text-primary/50 dark:text-emerald-500/50 transition-colors shadow-sm">Experimental</span>
                </div>
              </div>
            </div>
          </div>
          {/* Citation Item 3 */}
          <div className="p-4 rounded-xl border border-border-cream dark:border-gray-800 bg-white dark:bg-background-dark hover:border-primary/30 dark:hover:border-emerald-500/30 transition-colors cursor-pointer group shadow-sm">
            <div className="flex items-start gap-3">
              <div className="size-6 rounded bg-primary dark:bg-emerald-600 text-white flex items-center justify-center text-[10px] font-bold shrink-0 shadow-sm">3</div>
              <div className="space-y-1">
                <p className="text-xs font-bold text-primary dark:text-emerald-300 leading-tight group-hover:text-accent dark:group-hover:text-emerald-400 transition-colors">Quantum Supremacy Using a Programmable Superconducting Processor</p>
                <p className="text-[10px] text-primary/60 dark:text-emerald-500/60 transition-colors">Arute, F., et al. (2019). Nature, 574(7779), 505-510.</p>
                <div className="pt-2 flex gap-2">
                  <span className="text-[9px] px-2 py-0.5 bg-white dark:bg-gray-800 border border-border-cream dark:border-gray-700 rounded text-primary/50 dark:text-emerald-500/50 transition-colors shadow-sm">Groundbreaking</span>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div className="mt-auto p-6 border-t border-border-cream dark:border-gray-800 transition-colors">
          <button className="w-full border border-primary/20 dark:border-emerald-600/30 text-primary dark:text-emerald-400 py-2.5 rounded-xl text-xs font-bold flex items-center justify-center gap-2 hover:bg-primary/5 dark:hover:bg-emerald-500/10 transition-colors">
            <span className="material-symbols-outlined text-sm">download</span>
            Export Bibliography (.bib)
          </button>
        </div>
      </aside>
    </div>
  );
}
