'use client';

import { useState, useRef, useEffect } from 'react';
import { useLanguage } from '@/lib/language-context';
import { useTheme } from '@/lib/theme-context';
import { useDispatch, useSelector } from 'react-redux';
import { logout } from '@/store/auth/auth-actions';
import { AppDispatch, RootState } from '@/store/store';
import { useRouter } from 'next/navigation';
import { Conversation } from './chat-layout';


interface ChatSidebarProps {
  conversations: Conversation[];
  isOpen: boolean;
  activeView: 'chat' | 'documents';
  onViewChange: (view: 'chat' | 'documents') => void;
  onNewConversation: () => void;
  onSelectConversation: (id: string) => void;
}

export function ChatSidebar({
  conversations,
  isOpen,
  activeView,
  onViewChange,
  onNewConversation,
  onSelectConversation,
}: ChatSidebarProps) {
  const { t, language, setLanguage, isRTL } = useLanguage();
  const { theme, setTheme, isDark } = useTheme();
  const dispatch = useDispatch<AppDispatch>();
  const { user } = useSelector((state: RootState) => state.auth);
  const router = useRouter();
  
  const [settingsOpen, setSettingsOpen] = useState(false);
  const settingsRef = useRef<HTMLDivElement>(null);

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
  const handleLogout = () => {
    dispatch(logout());
    router.push('/');
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
          
          <button 
            onClick={onNewConversation}
            className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors mt-6"
          >
            <span className="material-symbols-outlined text-[22px]">add_circle</span>
            <span className="text-sm font-medium">{t('chatNewConversation')}</span>
          </button>

          {/* Conversations list appended here */}
          <div className="mt-2 space-y-0.5">
            {conversations.map((conv) => (
              <button
                key={conv.id}
                onClick={() => onSelectConversation(conv.id)}
                className={`
                  w-full flex items-center gap-3 px-3 py-2 rounded-lg text-start transition-all duration-200
                  ${conv.active
                    ? 'bg-primary/5 text-primary border border-primary/20 dark:bg-primary/10 dark:text-primary-light dark:border-primary/30'
                    : 'text-slate-500 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800 border-transparent'
                  }
                `}
              >
                <div className="w-[22px]" /> {/* spacing to align with text */}
                <span className="text-sm font-medium truncate">{conv.title}</span>
              </button>
            ))}
          </div>

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
