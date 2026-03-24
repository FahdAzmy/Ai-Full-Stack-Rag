'use client';

import React, { useState, useRef, useEffect, useCallback, memo } from 'react';
import { useLanguage } from '@/lib/language-context';
import { useTheme } from '@/lib/theme-context';
import { useDispatch, useSelector } from 'react-redux';
import { logout } from '@/store/auth/auth-actions';
import { AppDispatch, RootState } from '@/store/store';
import { useRouter } from 'next/navigation';
import {
  createChat,
  fetchChat,
  deleteChat,
  renameChat,
} from '@/store/chat/chat-actions';
import { setActiveChat, setSidebarOpen } from '@/store/chat/chat-slice';

interface ChatSidebarProps {
  isOpen: boolean;
  activeView: 'chat' | 'documents';
}

export const ChatSidebar = memo(function ChatSidebar({ isOpen, activeView }: ChatSidebarProps) {
  const { t, language, setLanguage, isRTL } = useLanguage();
  const { theme, setTheme } = useTheme();
  const dispatch = useDispatch<AppDispatch>();
  const { user } = useSelector((state: RootState) => state.auth);
  const { chats: rawChats, activeChat, loading } = useSelector((state: RootState) => state.chat);
  const chats = Array.isArray(rawChats) ? rawChats : [];
  const router = useRouter();

  const [settingsOpen, setSettingsOpen] = useState(false);
  const [renamingId, setRenamingId] = useState<string | null>(null);
  const [renameValue, setRenameValue] = useState('');
  const [confirmDeleteId, setConfirmDeleteId] = useState<string | null>(null);
  const settingsRef = useRef<HTMLDivElement>(null);
  const renameInputRef = useRef<HTMLInputElement>(null);

  const handleCloseMobile = useCallback(() => {
    if (window.innerWidth < 1024) {
      dispatch(setSidebarOpen(false));
    }
  }, [dispatch]);

  // Close settings when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (settingsRef.current && !settingsRef.current.contains(event.target as Node)) {
        setSettingsOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Focus rename input when it appears
  useEffect(() => {
    if (renamingId && renameInputRef.current) {
      renameInputRef.current.focus();
      renameInputRef.current.select();
    }
  }, [renamingId]);

  const handleLogout = useCallback(() => {
    dispatch(logout());
    router.push('/');
  }, [dispatch, router]);

  const handleNewChat = useCallback(() => {
    dispatch(setActiveChat(null));
    router.push('/chat');
    handleCloseMobile();
  }, [dispatch, router, handleCloseMobile]);

  const handleSelectChat = useCallback((chatId: string) => {
    dispatch(fetchChat(chatId));
    router.push('/chat');
    handleCloseMobile();
  }, [dispatch, router, handleCloseMobile]);

  const handleDeleteChat = useCallback((chatId: string) => {
    if (confirmDeleteId === chatId) {
      dispatch(deleteChat(chatId));
      setConfirmDeleteId(null);
    } else {
      setConfirmDeleteId(chatId);
      setTimeout(() => setConfirmDeleteId(null), 3000);
    }
  }, [confirmDeleteId, dispatch]);

  const handleStartRename = useCallback((chatId: string, currentTitle: string | null) => {
    setRenamingId(chatId);
    setRenameValue(currentTitle || '');
  }, []);

  const handleSubmitRename = useCallback(() => {
    if (renamingId && renameValue.trim()) {
      dispatch(renameChat({ id: renamingId, title: renameValue.trim() }));
    }
    setRenamingId(null);
    setRenameValue('');
  }, [renamingId, renameValue, dispatch]);

  const toggleSettings = useCallback(() => {
    setSettingsOpen(prev => !prev);
  }, []);

  const formatDate = useCallback((dateStr: string | null) => {
    if (!dateStr) return '';
    try {
      const date = new Date(dateStr);
      const now = new Date();
      const diffMs = now.getTime() - date.getTime();
      const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

      if (diffDays === 0) return t('today') || 'Today';
      if (diffDays === 1) return t('yesterday') || 'Yesterday';
      if (diffDays < 7) return `${diffDays}d ago`;
      return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    } catch {
      return '';
    }
  }, [t]);

  return (
    <>
      {/* Mobile overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/30 z-20 lg:hidden"
          onClick={() => dispatch(setSidebarOpen(false))}
          aria-hidden="true"
        />
      )}

      {/* Sidebar */}
      <aside
        className={`
          w-64 flex-shrink-0 border-r border-slate-200 dark:border-gray-800 bg-white dark:bg-gray-950 flex flex-col 
          transition-all duration-300 ease-in-out z-30 h-full
          ${isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0 lg:w-0 lg:border-0 lg:overflow-hidden'}
          fixed lg:relative inset-y-0 start-0 lg:inset-auto
        `}
        role="complementary"
        aria-label="Chat sidebar"
        aria-hidden={!isOpen}
      >
        <div className="p-6">
          <div className="flex items-center gap-3">
            <div className="bg-primary rounded-lg p-1.5 flex items-center justify-center text-white shadow-sm">
              <span className="material-symbols-outlined" aria-hidden="true">auto_stories</span>
            </div>
            <div>
              <h1 className="text-slate-900 dark:text-slate-100 text-base font-bold leading-tight">{t('scholarGpt') || 'AskAnyDoc'}</h1>
              <p className="text-slate-500 dark:text-slate-400 text-xs font-medium">{t('academicWorkspace')}</p>
            </div>
          </div>
        </div>
        
        <nav className="flex-1 px-3 space-y-1 overflow-y-auto chat-scrollbar pb-4" aria-label="Sidebar navigation">
          {/* Documents nav */}
          <button 
            onClick={() => router.push('/documents')}
            aria-current={activeView === 'documents' ? 'page' : undefined}
            className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg transition-colors ${activeView === 'documents' ? 'bg-primary/10 text-primary dark:bg-primary/20 dark:text-primary-light' : 'text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800'}`}
          >
            <span className="material-symbols-outlined text-[22px]" aria-hidden="true">description</span>
            <span className="text-sm font-semibold">{t('chatDocuments')}</span>
          </button>
          
          {/* New Chat button */}
          <button 
            onClick={handleNewChat}
            disabled={loading}
            aria-label={t('chatNewConversation') || 'Start new conversation'}
            className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors mt-6 disabled:opacity-50"
          >
            <span className="material-symbols-outlined text-[22px]" aria-hidden="true">add_circle</span>
            <span className="text-sm font-medium">{t('chatNewConversation')}</span>
          </button>

          {/* Chat list */}
          <div className="mt-2 space-y-0.5" role="list" aria-label="Chat history">
            {loading && chats.length === 0 ? (
              <div className="space-y-1 px-3" role="status" aria-label="Loading chats">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="animate-pulse h-9 bg-slate-100 dark:bg-slate-800 rounded-lg" aria-hidden="true" />
                ))}
                <span className="sr-only">Loading chats...</span>
              </div>
            ) : chats.length === 0 ? (
              <div className="px-3 py-6 text-center">
                <p className="text-xs text-slate-400 dark:text-slate-500">
                  {t('chatEmptyState') || 'No conversations yet. Start a new one!'}
                </p>
              </div>
            ) : (
              chats.map((chat) => {
                const isActive = activeChat?.id === chat.id;
                const isRenaming = renamingId === chat.id;

                return (
                  <div
                    key={chat.id}
                    role="listitem"
                    className={`
                      group relative flex items-center gap-2 px-3 py-2 rounded-lg text-start transition-all duration-200
                      ${isActive
                        ? 'bg-primary/5 text-primary border border-primary/20 dark:bg-primary/10 dark:text-primary-light dark:border-primary/30'
                        : 'text-slate-500 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800 border border-transparent'
                      }
                    `}
                  >
                    {isRenaming ? (
                      <input
                        ref={renameInputRef}
                        value={renameValue}
                        onChange={(e) => setRenameValue(e.target.value)}
                        onBlur={handleSubmitRename}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter') handleSubmitRename();
                          if (e.key === 'Escape') {
                            setRenamingId(null);
                            setRenameValue('');
                          }
                        }}
                        aria-label="Rename chat"
                        className="flex-1 text-sm font-medium bg-white dark:bg-slate-800 border border-primary/30 rounded px-2 py-0.5 outline-none focus:ring-1 focus:ring-primary/30"
                      />
                    ) : (
                      <button
                        onClick={() => handleSelectChat(chat.id)}
                        className="flex-1 min-w-0 text-start"
                        aria-current={isActive ? 'true' : undefined}
                        aria-label={`Open chat: ${chat.title || 'Untitled Chat'}`}
                      >
                        <p className="text-sm font-medium truncate">
                          {chat.title || t('untitledChat') || 'Untitled Chat'}
                        </p>
                        <p className="text-[10px] text-slate-400 dark:text-slate-500">
                          {formatDate(chat.last_message_at || chat.created_at)}
                          {chat.message_count > 0 && ` • ${chat.message_count} ${t('chatMsgCount') || 'msgs'}`}
                        </p>
                      </button>
                    )}

                    {/* Action buttons (visible on hover) */}
                    {!isRenaming && (
                      <div className="flex gap-0.5 opacity-0 group-hover:opacity-100 focus-within:opacity-100 transition-opacity shrink-0">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleStartRename(chat.id, chat.title);
                          }}
                          className="p-1 text-slate-400 hover:text-primary rounded transition-colors"
                          aria-label={`Rename chat: ${chat.title || 'Untitled Chat'}`}
                        >
                          <span className="material-symbols-outlined text-[16px]" aria-hidden="true">edit</span>
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleDeleteChat(chat.id);
                          }}
                          className={`p-1 rounded transition-colors ${
                            confirmDeleteId === chat.id
                              ? 'text-red-500 bg-red-50 dark:bg-red-900/20'
                              : 'text-slate-400 hover:text-red-500'
                          }`}
                          aria-label={
                            confirmDeleteId === chat.id
                              ? `Confirm delete: ${chat.title || 'Untitled Chat'}`
                              : `Delete chat: ${chat.title || 'Untitled Chat'}`
                          }
                        >
                          <span className="material-symbols-outlined text-[16px]" aria-hidden="true">
                            {confirmDeleteId === chat.id ? 'delete_forever' : 'delete'}
                          </span>
                        </button>
                      </div>
                    )}
                  </div>
                );
              })
            )}
          </div>

          {/* Configuration section */}
          <div className="pt-4 pb-2 px-3 text-[11px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider">
            {t('chatConfiguration')}
          </div>
          
          <div className="relative" ref={settingsRef}>
             {/* Settings Popover */}
             {settingsOpen && (
               <div
                 className={`absolute bottom-full mb-2 ${isRTL ? 'right-0' : 'left-0'} w-56 bg-white dark:bg-slate-800 rounded-2xl shadow-xl border border-slate-200 dark:border-slate-700 p-2 z-[60] animate-in fade-in slide-in-from-bottom-2 duration-200`}
                 role="dialog"
                 aria-label="Settings"
               >
                 <div className="p-2">
                   <p className="px-2 pb-2 text-[10px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider" id="lang-label">
                     {t('language')}
                   </p>
                   <div className="grid grid-cols-2 gap-1 bg-slate-50 dark:bg-slate-900/50 p-1 rounded-xl" role="radiogroup" aria-labelledby="lang-label">
                     <button 
                       onClick={() => setLanguage('en')}
                       role="radio"
                       aria-checked={language === 'en'}
                       className={`flex items-center justify-center gap-1.5 py-2 px-1 rounded-lg text-xs font-medium transition-all ${language === 'en' ? 'bg-white dark:bg-slate-700 text-primary shadow-sm' : 'text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-300'}`}
                     >
                       English
                     </button>
                     <button 
                       onClick={() => setLanguage('ar')}
                       role="radio"
                       aria-checked={language === 'ar'}
                       className={`flex items-center justify-center gap-1.5 py-2 px-1 rounded-lg text-xs font-medium transition-all ${language === 'ar' ? 'bg-white dark:bg-slate-700 text-primary shadow-sm' : 'text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-300'}`}
                     >
                       العربية
                     </button>
                   </div>
                 </div>

                 <div className="p-2 border-t border-slate-50 dark:border-slate-700/50">
                   <p className="px-2 pb-2 text-[10px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider" id="theme-label">
                     {t('theme') || 'Theme'}
                   </p>
                   <div className="grid grid-cols-3 gap-1 bg-slate-50 dark:bg-slate-900/50 p-1 rounded-xl" role="radiogroup" aria-labelledby="theme-label">
                     <button 
                       onClick={() => setTheme('light')}
                       role="radio"
                       aria-checked={theme === 'light'}
                       aria-label={t('lightTheme') || 'Light theme'}
                       className={`flex items-center justify-center p-2 rounded-lg transition-all ${theme === 'light' ? 'bg-white dark:bg-slate-700 text-primary shadow-sm' : 'text-slate-400 hover:text-slate-600 dark:text-slate-500 dark:hover:text-slate-300'}`}
                     >
                       <span className="material-symbols-outlined text-base" aria-hidden="true">light_mode</span>
                     </button>
                     <button 
                       onClick={() => setTheme('dark')}
                       role="radio"
                       aria-checked={theme === 'dark'}
                       aria-label={t('darkTheme') || 'Dark theme'}
                       className={`flex items-center justify-center p-2 rounded-lg transition-all ${theme === 'dark' ? 'bg-white dark:bg-slate-700 text-primary shadow-sm' : 'text-slate-400 hover:text-slate-600 dark:text-slate-500 dark:hover:text-slate-300'}`}
                     >
                       <span className="material-symbols-outlined text-base" aria-hidden="true">dark_mode</span>
                     </button>
                     <button 
                       onClick={() => setTheme('system')}
                       role="radio"
                       aria-checked={theme === 'system'}
                       aria-label={t('systemTheme') || 'System theme'}
                       className={`flex items-center justify-center p-2 rounded-lg transition-all ${theme === 'system' ? 'bg-white dark:bg-slate-700 text-primary shadow-sm' : 'text-slate-400 hover:text-slate-600 dark:text-slate-500 dark:hover:text-slate-300'}`}
                     >
                       <span className="material-symbols-outlined text-base" aria-hidden="true">settings_brightness</span>
                     </button>
                   </div>
                 </div>
               </div>
             )}
             
             <button 
               onClick={toggleSettings}
               aria-expanded={settingsOpen}
               aria-label={t('chatSettings') || 'Settings'}
               className="w-full flex items-center justify-between gap-3 px-3 py-2 rounded-lg text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors"
             >
              <div className="flex items-center gap-3">
               <span className="material-symbols-outlined text-[22px]" aria-hidden="true">settings</span>
               <span className="text-sm font-medium">{t('chatSettings')}</span>
              </div>
              <span className={`material-symbols-outlined text-[18px] transition-transform ${settingsOpen ? 'rotate-90' : isRTL ? 'rotate-180' : ''}`} aria-hidden="true">chevron_right</span>
             </button>
          </div>
        </nav>

        {/* User footer */}
        <div className="p-4 border-t border-slate-200 dark:border-slate-800">
          <div className="flex items-center gap-3 p-2">
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium truncate text-slate-900 dark:text-slate-100">{user?.name || t('guestUser')}</p>
              <p className="text-xs text-slate-500 dark:text-slate-400 truncate">{user?.email || t('freePlan')}</p>
            </div>
            <button
               onClick={handleLogout}
               aria-label={t('chatLogout') || 'Log out'}
               className="text-slate-400 hover:text-red-500 dark:text-slate-500 dark:hover:text-red-400 transition-colors shrink-0"
            >
               <span className="material-symbols-outlined text-[20px]" aria-hidden="true">logout</span>
            </button>
          </div>
        </div> 
      </aside>
    </>
  );
});
