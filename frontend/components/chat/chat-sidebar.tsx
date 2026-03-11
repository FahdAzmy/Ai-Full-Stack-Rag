'use client';

import { useState, useRef, useEffect } from 'react';
import { useLanguage } from '@/lib/language-context';
import { useTheme } from '@/lib/theme-context';
import { useDispatch, useSelector } from 'react-redux';
import { logout } from '@/store/auth/auth-actions';
import { AppDispatch, RootState } from '@/store/store';
import { useRouter } from 'next/navigation';
import {
  fetchChats,
  createChat,
  fetchChat,
  deleteChat,
  renameChat,
} from '@/store/chat/chat-actions';

interface ChatSidebarProps {
  isOpen: boolean;
  activeView: 'chat' | 'documents';
}

export function ChatSidebar({ isOpen, activeView }: ChatSidebarProps) {
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

  // Fetch chats on mount
  useEffect(() => {
    dispatch(fetchChats());
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

  const handleLogout = () => {
    dispatch(logout());
    router.push('/');
  };

  const handleNewChat = async () => {
    await dispatch(createChat(undefined));
    router.push('/chat');
  };

  const handleSelectChat = (chatId: string) => {
    dispatch(fetchChat(chatId));
    router.push('/chat');
  };

  const handleDeleteChat = (chatId: string) => {
    if (confirmDeleteId === chatId) {
      dispatch(deleteChat(chatId));
      setConfirmDeleteId(null);
    } else {
      setConfirmDeleteId(chatId);
      setTimeout(() => setConfirmDeleteId(null), 3000);
    }
  };

  const handleStartRename = (chatId: string, currentTitle: string | null) => {
    setRenamingId(chatId);
    setRenameValue(currentTitle || '');
  };

  const handleSubmitRename = () => {
    if (renamingId && renameValue.trim()) {
      dispatch(renameChat({ id: renamingId, title: renameValue.trim() }));
    }
    setRenamingId(null);
    setRenameValue('');
  };

  const formatDate = (dateStr: string | null) => {
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
  };

  return (
    <>
      {/* Mobile overlay */}
      {isOpen && (
        <div className="fixed inset-0 bg-black/30 z-20 lg:hidden" onClick={() => {}} />
      )}

      {/* Sidebar */}
      <aside className={`
        w-64 flex-shrink-0 border-r border-slate-200 dark:border-gray-800 bg-white dark:bg-gray-950 flex flex-col 
        transition-all duration-300 ease-in-out z-30 h-full
        ${isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0 lg:w-0 lg:border-0 lg:overflow-hidden'}
        fixed lg:relative inset-y-0 start-0 lg:inset-auto
      `}>
        <div className="p-6">
          <div className="flex items-center gap-3">
            <div className="bg-primary rounded-lg p-1.5 flex items-center justify-center text-white shadow-sm">
              <span className="material-symbols-outlined">auto_stories</span>
            </div>
            <div>
              <h1 className="text-slate-900 dark:text-slate-100 text-base font-bold leading-tight">{t('scholarGpt') || 'ScholarGPT'}</h1>
              <p className="text-slate-500 dark:text-slate-400 text-xs font-medium">{t('academicWorkspace')}</p>
            </div>
          </div>
        </div>
        
        <nav className="flex-1 px-3 space-y-1 overflow-y-auto chat-scrollbar pb-4">
          {/* Navigation buttons */}
          <button 
            onClick={() => router.push('/chat')}
            className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg transition-colors ${activeView === 'chat' ? 'bg-primary/10 text-primary dark:bg-primary/20 dark:text-primary-light' : 'text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800'}`}
          >
            <span className="material-symbols-outlined text-[22px]">chat_bubble</span>
            <span className="text-sm font-medium">{t('chatChats')}</span>
          </button>
          
          <button 
            onClick={() => router.push('/documents')}
            className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg transition-colors ${activeView === 'documents' ? 'bg-primary/10 text-primary dark:bg-primary/20 dark:text-primary-light' : 'text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800'}`}
          >
            <span className="material-symbols-outlined text-[22px]">description</span>
            <span className="text-sm font-semibold">{t('chatDocuments')}</span>
          </button>
          
          {/* New Chat button */}
          <button 
            onClick={handleNewChat}
            disabled={loading}
            className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors mt-6 disabled:opacity-50"
          >
            <span className="material-symbols-outlined text-[22px]">add_circle</span>
            <span className="text-sm font-medium">{t('chatNewConversation')}</span>
          </button>

          {/* Chat list */}
          <div className="mt-2 space-y-0.5">
            {loading && chats.length === 0 ? (
              // Skeleton loader
              <div className="space-y-1 px-3">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="animate-pulse h-9 bg-slate-100 dark:bg-slate-800 rounded-lg" />
                ))}
              </div>
            ) : chats.length === 0 ? (
              // Empty state
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
                        className="flex-1 text-sm font-medium bg-white dark:bg-slate-800 border border-primary/30 rounded px-2 py-0.5 outline-none focus:ring-1 focus:ring-primary/30"
                      />
                    ) : (
                      <button
                        onClick={() => handleSelectChat(chat.id)}
                        className="flex-1 min-w-0 text-start"
                      >
                        <p className="text-sm font-medium truncate">
                          {chat.title || t('untitledChat') || 'Untitled Chat'}
                        </p>
                        <p className="text-[10px] text-slate-400 dark:text-slate-500">
                          {formatDate(chat.last_message_at || chat.created_at)}
                          {chat.message_count > 0 && ` • ${chat.message_count} msgs`}
                        </p>
                      </button>
                    )}

                    {/* Action buttons (visible on hover) */}
                    {!isRenaming && (
                      <div className="flex gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity shrink-0">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleStartRename(chat.id, chat.title);
                          }}
                          className="p-1 text-slate-400 hover:text-primary rounded transition-colors"
                          title={t('chatRename') || 'Rename'}
                        >
                          <span className="material-symbols-outlined text-[16px]">edit</span>
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
                          title={confirmDeleteId === chat.id ? (t('chatConfirmDelete') || 'Click to confirm') : (t('chatDelete') || 'Delete')}
                        >
                          <span className="material-symbols-outlined text-[16px]">
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
          <div className="pt-4 pb-2 px-3 text-[11px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider">{t('chatConfiguration')}</div>
          
          <div className="relative" ref={settingsRef}>
             {/* Settings Popover */}
             {settingsOpen && (
               <div className={`absolute bottom-full mb-2 ${isRTL ? 'right-0' : 'left-0'} w-56 bg-white dark:bg-slate-800 rounded-2xl shadow-xl border border-slate-200 dark:border-slate-700 p-2 z-[60] animate-in fade-in slide-in-from-bottom-2 duration-200`}>
                 <div className="p-2">
                   <p className="px-2 pb-2 text-[10px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider">
                     {t('language')}
                   </p>
                   <div className="grid grid-cols-2 gap-1 bg-slate-50 dark:bg-slate-900/50 p-1 rounded-xl">
                     <button 
                       onClick={() => setLanguage('en')}
                       className={`flex items-center justify-center gap-1.5 py-2 px-1 rounded-lg text-xs font-medium transition-all ${language === 'en' ? 'bg-white dark:bg-slate-700 text-primary shadow-sm' : 'text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-300'}`}
                     >
                       English
                     </button>
                     <button 
                       onClick={() => setLanguage('ar')}
                       className={`flex items-center justify-center gap-1.5 py-2 px-1 rounded-lg text-xs font-medium transition-all ${language === 'ar' ? 'bg-white dark:bg-slate-700 text-primary shadow-sm' : 'text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-300'}`}
                     >
                       العربية
                     </button>
                   </div>
                 </div>

                 <div className="p-2 border-t border-slate-50 dark:border-slate-700/50">
                   <p className="px-2 pb-2 text-[10px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider">
                     Theme
                   </p>
                   <div className="grid grid-cols-3 gap-1 bg-slate-50 dark:bg-slate-900/50 p-1 rounded-xl">
                     <button 
                       onClick={() => setTheme('light')}
                       className={`flex items-center justify-center p-2 rounded-lg transition-all ${theme === 'light' ? 'bg-white dark:bg-slate-700 text-primary shadow-sm' : 'text-slate-400 hover:text-slate-600 dark:text-slate-500 dark:hover:text-slate-300'}`}
                       title="Light"
                     >
                       <span className="material-symbols-outlined text-base">light_mode</span>
                     </button>
                     <button 
                       onClick={() => setTheme('dark')}
                       className={`flex items-center justify-center p-2 rounded-lg transition-all ${theme === 'dark' ? 'bg-white dark:bg-slate-700 text-primary shadow-sm' : 'text-slate-400 hover:text-slate-600 dark:text-slate-500 dark:hover:text-slate-300'}`}
                       title="Dark"
                     >
                       <span className="material-symbols-outlined text-base">dark_mode</span>
                     </button>
                     <button 
                       onClick={() => setTheme('system')}
                       className={`flex items-center justify-center p-2 rounded-lg transition-all ${theme === 'system' ? 'bg-white dark:bg-slate-700 text-primary shadow-sm' : 'text-slate-400 hover:text-slate-600 dark:text-slate-500 dark:hover:text-slate-300'}`}
                       title="System"
                     >
                       <span className="material-symbols-outlined text-base">settings_brightness</span>
                     </button>
                   </div>
                 </div>
               </div>
             )}
             
             <button 
               onClick={() => setSettingsOpen(!settingsOpen)}
               className="w-full flex items-center justify-between gap-3 px-3 py-2 rounded-lg text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors"
             >
              <div className="flex items-center gap-3">
               <span className="material-symbols-outlined text-[22px]">settings</span>
               <span className="text-sm font-medium">{t('chatSettings')}</span>
              </div>
              <span className={`material-symbols-outlined text-[18px] transition-transform ${settingsOpen ? 'rotate-90' : isRTL ? 'rotate-180' : ''}`}>chevron_right</span>
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
               title={t('chatLogout')}
               className="text-slate-400 hover:text-red-500 dark:text-slate-500 dark:hover:text-red-400 transition-colors shrink-0"
            >
               <span className="material-symbols-outlined text-[20px]">logout</span>
            </button>
          </div>
        </div> 
      </aside>
    </>
  );
}
